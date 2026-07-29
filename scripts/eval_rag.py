#!/usr/bin/env python3
"""Automated RAG evaluation script.

Measures production RAG quality against a ground-truth dataset.
Reports faithfullness, answer relevance, citation precision, and latency.

Usage:
    # Against an already-running dev server with documents already uploaded:
    python scripts/eval_rag.py --report-ids "uuid1,uuid2,uuid3"

    # With re-upload of test PDFs:
    python scripts/eval_rag.py --upload --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import httpx

# ── Config ─────────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DATA_DIR = PROJECT_ROOT / "test_data" / "rag_eval"
TEST_DATA_DIR = PROJECT_ROOT / "test_data"


# ── Scoring helpers ────────────────────────────────────────────────────────────


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb + 1e-12)


def _estimate_faithfulness(answer: str, chunks: list[dict[str, Any]]) -> float:
    """Estimate faithfulness as the fraction of answer claims supported by chunks.

    Uses simple n-gram overlap as a proxy.  In production this should use
    an LLM judge or dedicated faithfulness model (e.g. TrueTeacher).
    """
    if not chunks:
        return 0.0
    chunk_text = " ".join(c.get("content", "") for c in chunks).lower()
    # Count significant words (not stopwords) from answer that appear in chunks
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "and", "but", "or",
        "if", "because", "about", "up", "it", "its", "that", "this",
        "what", "which", "who", "whom", "i", "you", "he", "she", "we",
        "they", "me", "him", "her", "us", "them", "my", "your", "his",
        "my", "our", "their",
    }
    answer_words = [w.lower().strip(".,!?;:'\"") for w in answer.split()]
    answer_words = [w for w in answer_words if len(w) > 2 and w not in stopwords]
    if not answer_words:
        return 1.0
    supported = sum(1 for w in answer_words if w in chunk_text)
    return supported / len(answer_words)


def _answer_relevance(answer: str, expected_topics: list[str]) -> float:
    """Score answer relevance by topic overlap."""
    if not expected_topics:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for topic in expected_topics if topic.lower() in answer_lower)
    return hits / len(expected_topics)


def _citation_precision(citations: list[dict[str, Any]]) -> float:
    """Score how many chunks have usable citation metadata."""
    if not citations:
        return 0.0
    meaningful = sum(
        1 for c in citations if c.get("chunk_id") and c.get("score", 0) > 0.01
    )
    return meaningful / len(citations)


# ── API helpers ────────────────────────────────────────────────────────────────


async def _upload_pdf(
    client: httpx.AsyncClient,
    base_url: str,
    pdf_path: str,
    token: str,
) -> str | None:
    """Upload a PDF and return report_id, or None on failure."""
    url = f"{base_url}/api/v1/reports"
    headers = {"Authorization": f"Bearer {token}"}
    fname = os.path.basename(pdf_path)
    files = {"file": (fname, open(pdf_path, "rb"), "application/pdf")}
    data = {"title": fname, "description": f"Eval upload: {fname}"}

    resp = await client.post(url, headers=headers, files=files, data=data)
    if resp.status_code not in (200, 201):
        print(f"  ✘ Upload failed ({resp.status_code}): {resp.text[:200]}")
        return None
    body = resp.json()
    rid = body.get("id")
    print(f"  ✓ Uploaded {fname} → report_id={rid}")
    return rid


async def _wait_ready(
    client: httpx.AsyncClient,
    base_url: str,
    report_id: str,
    token: str,
    timeout: float = 120.0,
) -> bool:
    """Poll until report status is 'ready'."""
    url = f"{base_url}/api/v1/reports/{report_id}"
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            await asyncio.sleep(2)
            continue
        body = resp.json()
        status = body.get("status", "")
        if status == "ready":
            return True
        if status == "failed":
            print(f"  ✘ Report {report_id} processing failed")
            return False
        await asyncio.sleep(3)
    print(f"  ✘ Report {report_id} not ready after {timeout}s")
    return False


async def _ask(
    client: httpx.AsyncClient,
    base_url: str,
    query: str,
    report_ids: list[str],
    token: str,
) -> dict[str, Any]:
    """Send a query and return structured result."""
    url = f"{base_url}/api/v1/chat/send"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "message": query,
        "report_ids": report_ids,
        "mode": "single",
    }
    t0 = time.monotonic()
    resp = await client.post(url, headers=headers, json=payload)
    elapsed = (time.monotonic() - t0) * 1000

    if resp.status_code != 200:
        return {"error": f"API error {resp.status_code}: {resp.text[:200]}", "latency_ms": elapsed}

    body = resp.json()
    msg = body.get("message", {})
    citations = body.get("citations", body.get("citations", [])) or msg.get("citations", [])

    return {
        "answer": msg.get("content", ""),
        "citations": citations,
        "latency_ms": elapsed,
    }


# ── Main evaluator ─────────────────────────────────────────────────────────────


async def evaluate(
    base_url: str,
    report_ids: list[str] | None = None,
    upload: bool = False,
    token: str | None = None,
) -> dict[str, Any]:
    """Run evaluation against ground-truth dataset."""

    # Resolve token
    if token is None:
        try:
            token = Path("/tmp/token.txt").read_text().strip()
        except FileNotFoundError:
            token = ""

    if not token:
        print("⚠  No auth token. Set --token or place in /tmp/token.txt")
        return {}

    # Load ground truth datasets
    datasets: list[dict[str, Any]] = []
    for fpath in sorted(EVAL_DATA_DIR.glob("*.json")):
        with open(fpath) as f:
            datasets.append(json.load(f))

    print(f"\n{'='*60}")
    print("RAG EVALUATION")
    print(f"{'='*60}")
    print(f"Datasets: {len(datasets)}")
    print(f"Total queries: {sum(len(d['queries']) for d in datasets)}")

    # Upload phase
    upload_ids: dict[str, str] = {}  # filename -> report_id
    actual_report_ids: list[str] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        if upload:
            print(f"\n{'─'*60}")
            print("Upload Phase")
            print(f"{'─'*60}")
            for ds in datasets:
                pdf_rel = ds["document_path"]
                pdf_path = str(PROJECT_ROOT / pdf_rel)
                if not os.path.exists(pdf_path):
                    print(f"  ⚠  File not found: {pdf_path}")
                    continue
                rid = await _upload_pdf(client, base_url, pdf_path, token)
                if rid:
                    upload_ids[os.path.basename(pdf_rel)] = rid
                    actual_report_ids.append(rid)

            if not actual_report_ids:
                print("  ✘ No documents uploaded, cannot evaluate")
                return {}

            print(f"\n  Waiting for processing to complete...")
            ready = await asyncio.gather(*[
                _wait_ready(client, base_url, rid, token)
                for rid in actual_report_ids
            ])
            if not all(ready):
                print("  ✘ Not all documents processed, results may be partial")

            # Map dataset -> report_id
            for ds in datasets:
                fname = os.path.basename(ds["document_path"])
                if fname in upload_ids:
                    ds["_report_id"] = upload_ids[fname]
        else:
            # Use provided report_ids
            if report_ids:
                print(f"\n  Using provided report IDs: {report_ids}")
                for i, ds in enumerate(datasets):
                    ds["_report_id"] = report_ids[i] if i < len(report_ids) else report_ids[0]

        # Evaluation phase
        print(f"\n{'─'*60}")
        print("Evaluation Phase")
        print(f"{'─'*60}")

        all_results: list[dict[str, Any]] = []
        for ds in datasets:
            rid = ds.get("_report_id")
            if not rid:
                print(f"  ⚠  No report_id for {ds['document']}, skipping")
                continue
            print(f"\n  Document: {ds['document']} (report_id={rid[:8]}...)")
            for q in ds["queries"]:
                result = await _ask(client, base_url, q["query"], [rid], token)
                result["query_id"] = q["id"]
                result["query"] = q["query"]
                result["expected_topics"] = q["expected_topics"]

                if "error" in result:
                    print(f"    ✘ {q['query'][:50]}: {result['error']}")
                else:
                    # Score
                    faith = _estimate_faithfulness(result.get("answer", ""), result.get("citations", []))
                    relevance = _answer_relevance(result.get("answer", ""), q["expected_topics"])
                    citation_prec = _citation_precision(result.get("citations", []))

                    result["faithfulness"] = round(faith, 3)
                    result["relevance"] = round(relevance, 3)
                    result["citation_precision"] = round(citation_prec, 3)

                    print(f"    {q['query'][:60]:60s} "
                          f"faith={faith:.2f} rel={relevance:.2f} "
                          f"cite={citation_prec:.2f} "
                          f"{result['latency_ms']:.0f}ms")

                all_results.append(result)

        # Aggregate report
        print(f"\n{'='*60}")
        print("REPORT")
        print(f"{'='*60}")

        completed = [r for r in all_results if "error" not in r]
        if not completed:
            print("  No completed queries to report.")
            return {}

        faithfulness_scores = [r["faithfulness"] for r in completed]
        relevance_scores = [r["relevance"] for r in completed]
        citation_scores = [r["citation_precision"] for r in completed]
        latencies = [r["latency_ms"] for r in completed]

        avg_faith = statistics.mean(faithfulness_scores)
        avg_rel = statistics.mean(relevance_scores)
        avg_cite = statistics.mean(citation_scores)
        p50_lat = statistics.median(latencies)
        p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
        overall = (avg_faith + avg_rel + avg_cite) / 3 * 10

        print(f"""
  ┌─────────────────────────────────────────────────┐
  │               EVALUATION SCORECARD                │
  ├────────────────────────────────┬────────────────┤
  │  Metric                        │  Score (0-10)  │
  ├────────────────────────────────┼────────────────┤
  │  Faithfulness                  │     {avg_faith*10:.1f}           │
  │  Answer Relevance              │     {avg_rel*10:.1f}           │
  │  Citation Precision            │     {avg_cite*10:.1f}           │
  ├────────────────────────────────┼────────────────┤
  │  OVERALL                       │     {overall:.1f}           │
  └────────────────────────────────┴────────────────┘

  Queries: {len(completed)}/{len(all_results)} completed
  Latency: p50={p50_lat:.0f}ms  p95={p95_lat:.0f}ms
""")

        # Save detailed results
        out_path = Path.cwd() / "rag_eval_results.json"
        with open(out_path, "w") as f:
            json.dump({
                "overall": round(overall, 1),
                "faithfulness_avg": round(avg_faith, 3),
                "relevance_avg": round(avg_rel, 3),
                "citation_precision_avg": round(avg_cite, 3),
                "latency_p50_ms": round(p50_lat, 0),
                "latency_p95_ms": round(p95_lat, 0),
                "results": all_results,
            }, f, indent=2)
        print(f"  Detailed results saved to: {out_path}")

        return {
            "overall": overall,
            "faithfulness": avg_faith,
            "relevance": avg_rel,
            "citation_precision": avg_cite,
            "latency_p50": p50_lat,
            "latency_p95": p95_lat,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG evaluation pipeline")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--report-ids", help="Comma-separated report UUIDs to test against")
    parser.add_argument("--upload", action="store_true", help="Upload test PDFs before eval")
    parser.add_argument("--token", help="Auth token (default: /tmp/token.txt)")
    args = parser.parse_args()

    report_ids = args.report_ids.split(",") if args.report_ids else None
    asyncio.run(evaluate(
        base_url=args.base_url,
        report_ids=report_ids,
        upload=args.upload,
        token=args.token or None,
    ))


if __name__ == "__main__":
    main()
