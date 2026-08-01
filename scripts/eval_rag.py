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
import functools
import json
import logging
import math
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import httpx

# ── Config ─────────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8000"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"

# OpenCode Zen (optional judge provider — set OPENCODE_ZEN_API_KEY env var to use)
OPENCODE_ZEN_BASE_URL = "https://opencode.ai/zen/v1"
OPENCODE_ZEN_MODEL = "deepseek-v4-flash-free"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DATA_DIR = PROJECT_ROOT / "test_data" / "rag_eval"
TEST_DATA_DIR = PROJECT_ROOT / "test_data"


# ── Scoring helpers ────────────────────────────────────────────────────────────


async def _llm_judge(
    system_prompt: str,
    user_prompt: str,
    client: httpx.AsyncClient,
    provider: str = "ollama",
) -> float:
    """Call an LLM judge, return YES=1.0 / NO=0.0.

    Supports ``ollama`` (default) and ``opencode_zen`` providers.
    """
    if provider == "opencode_zen":
        api_key = os.environ.get("OPENCODE_ZEN_API_KEY", "")
        if not api_key:
            logger = logging.getLogger(__name__)
            logger.warning("OPENCODE_ZEN_API_KEY not set, falling back to 0.0")
            return 0.0
        payload = {
            "model": OPENCODE_ZEN_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 64,
            "stream": False,
        }
        # DeepSeek reasoning models use high token budget for reasoning
        payload["max_tokens"] = 1024
        try:
            resp = await client.post(
                f"{OPENCODE_ZEN_BASE_URL}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=60.0,
            )
            if resp.status_code != 200:
                logger = logging.getLogger(__name__)
                logger.warning("Zen judge returned %d: %s", resp.status_code, resp.text[:200])
                return 0.0
            body = resp.json()
            msg = body.get("choices", [{}])[0].get("message", {})
            # Reasoning models (DeepSeek) emit the clean YES/NO in `content`;
            # `reasoning_content` holds the reasoning trace (prose, never
            # starts with YES/NO). Read content first, fall back only if empty.
            content = (msg.get("content") or msg.get("reasoning_content") or "").strip().upper()
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("Zen judge failed: %s", exc)
            return 0.0
    else:
        # Ollama
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.0},
        }
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=30.0)
            if resp.status_code != 200:
                logger = logging.getLogger(__name__)
                logger.warning("Ollama judge returned %d: %s", resp.status_code, resp.text[:200])
                return 0.0
            body = resp.json()
            content = body.get("message", {}).get("content", "").strip().upper()
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("Ollama judge failed: %s", exc)
            return 0.0

    # Parse: YES=1.0 / NO=0.0 / numeric fallback
    if content.startswith("YES"):
        return 1.0
    if content.startswith("NO"):
        return 0.0
    match = re.search(r"([01]\.?\d*)", content)
    score = float(match.group(1)) if match else 0.0
    return max(0.0, min(1.0, score))


async def _llm_faithfulness(
    answer: str,
    chunks: list[dict],
    client: httpx.AsyncClient,
    provider: str = "ollama",
) -> float:
    """Judge answer faithfulness via LLM (YES/NO → 1.0/0.0)."""
    if not chunks:
        return 0.0
    chunk_text = "\n".join(
        f"[{i + 1}] {c.get('content', '')[:8000]}"
        for i, c in enumerate(chunks[:5])
    )
    system = (
        "You are a faithfulness evaluator. Answer only YES or NO. "
        "YES = every claim in the answer is supported by the excerpts. "
        "NO = any claim is not supported or contradicts the excerpts."
    )
    user = f"Excerpts:\n{chunk_text}\n\nAnswer:\n{answer}\n\nIs every claim in the answer supported by the excerpts? Answer YES or NO:"
    return await _llm_judge(system, user, client, provider=provider)


async def _llm_answer_relevance(
    answer: str,
    query: str,
    client: httpx.AsyncClient,
    provider: str = "ollama",
) -> float:
    """Judge answer relevance via LLM (YES/NO → 1.0/0.0)."""
    system = (
        "You are a relevance evaluator. Answer only YES or NO. "
        "YES = the answer meaningfully addresses the question. "
        "NO = the answer is irrelevant or evades the question."
    )
    user = f"Question: {query}\n\nAnswer: {answer}\n\nDoes the answer meaningfully address the question? Answer YES or NO:"
    return await _llm_judge(system, user, client, provider=provider)


@functools.lru_cache(maxsize=128)
def _compute_retrieval_metrics_from_citations(
    retrieved_chunk_ids: tuple[str, ...],
    cited_chunk_ids: tuple[str, ...],
    k: int = 10,
) -> dict[str, float]:
    """Compute Recall@K, MRR@K, nDCG@K using cited chunks as relevance signal.

    A chunk is "relevant" if it was actually cited by the LLM.
    Uses lru_cache so repeated queries with the same data don't re-compute.
    """
    relevant = {cid for cid in cited_chunk_ids}
    if not relevant:
        return {f"recall_at_{k}": 0.0, f"mrr_at_{k}": 0.0, f"ndcg_at_{k}": 0.0}

    # Binary relevance grades: 1 if cited, 0 otherwise
    grades = [1.0 if cid in relevant else 0.0 for cid in retrieved_chunk_ids]
    top_k_grades = grades[:k]

    # Recall@K
    total_relevant = len(relevant)
    found = sum(top_k_grades)
    recall = found / total_relevant if total_relevant > 0 else 0.0

    # MRR@K - reciprocal rank of first relevant
    mrr = 0.0
    for i, g in enumerate(top_k_grades):
        if g > 0:
            mrr = 1.0 / (i + 1)
            break

    # nDCG@K - discounted cumulative gain
    dcg = sum(g / math.log2(i + 2) for i, g in enumerate(top_k_grades))
    ideal = sorted(grades, reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    ndcg = dcg / idcg if idcg > 0 else 0.0

    return {
        f"recall_at_{k}": round(recall, 3),
        f"mrr_at_{k}": round(mrr, 3),
        f"ndcg_at_{k}": round(ndcg, 3),
    }


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
    judge_provider: str = "ollama",
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
    async with httpx.AsyncClient(timeout=120.0) as client:
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

        # Separate client for Ollama (longer timeout for LLM judge)
        ollama_client = httpx.AsyncClient(timeout=60.0)

        all_results: list[dict[str, Any]] = []
        all_retrieval_metrics: list[dict[str, float]] = []
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
                    # LLM-based scoring
                    ans = result.get("answer", "")
                    citations = result.get("citations", [])

                    faith = await _llm_faithfulness(ans, citations, ollama_client, provider=judge_provider)
                    relevance = await _llm_answer_relevance(ans, q["query"], ollama_client, provider=judge_provider)
                    citation_prec = _citation_precision(citations)

                    result["faithfulness"] = round(faith, 3)
                    result["relevance"] = round(relevance, 3)
                    result["citation_precision"] = round(citation_prec, 3)

                    # Retrieval metrics: search for ranked chunks + citation-based relevance
                    try:
                        search_url = f"{base_url}/api/v1/reports/{rid}/search"
                        search_headers = {"Authorization": f"Bearer {token}"}
                        search_resp = await client.post(
                            search_url,
                            headers=search_headers,
                            json={"query": q["query"], "top_k": 25},
                        )
                        if search_resp.status_code == 200:
                            search_body = search_resp.json()
                            search_chunks = search_body.get("chunks", [])
                            result["retrieved_chunks"] = len(search_chunks)

                            if search_chunks and citations:
                                retrieved_ids = tuple(c["chunk_id"] for c in search_chunks)
                                cited_ids = tuple(c.get("chunk_id", "") for c in citations)

                                rm5 = _compute_retrieval_metrics_from_citations(retrieved_ids, cited_ids, k=5)
                                rm10 = _compute_retrieval_metrics_from_citations(retrieved_ids, cited_ids, k=10)
                                result["retrieval_metrics"] = {**rm5, **rm10}
                                all_retrieval_metrics.append(result["retrieval_metrics"])
                                result["num_relevant_chunks"] = len({c.get("chunk_id") for c in citations})
                            else:
                                result["num_relevant_chunks"] = 0
                        else:
                            result["retrieved_chunks"] = 0
                    except Exception as exc:
                        logger = logging.getLogger(__name__)
                        logger.warning("Search/retrieval metrics failed for %s: %s", q["query"][:40], exc)
                        result["retrieved_chunks"] = 0

                    print(f"    {q['query'][:60]:60s} "
                          f"faith={faith:.2f} rel={relevance:.2f} "
                          f"cite={citation_prec:.2f} "
                          f"chunks={result.get('retrieved_chunks', 0):2d} "
                          f"{result['latency_ms']:.0f}ms")

                all_results.append(result)

        # Cleanup Ollama client
        await ollama_client.aclose()

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

        # Aggregate retrieval metrics
        if all_retrieval_metrics:
            avg_recall5 = statistics.mean(m.get("recall_at_5", 0) for m in all_retrieval_metrics)
            avg_recall10 = statistics.mean(m.get("recall_at_10", 0) for m in all_retrieval_metrics)
            avg_mrr5 = statistics.mean(m.get("mrr_at_5", 0) for m in all_retrieval_metrics)
            avg_mrr10 = statistics.mean(m.get("mrr_at_10", 0) for m in all_retrieval_metrics)
            avg_ndcg5 = statistics.mean(m.get("ndcg_at_5", 0) for m in all_retrieval_metrics)
            avg_ndcg10 = statistics.mean(m.get("ndcg_at_10", 0) for m in all_retrieval_metrics)
            avg_chunks = statistics.mean(
                r.get("retrieved_chunks", 0) for r in completed
            )
            avg_relevant = statistics.mean(
                r.get("num_relevant_chunks", 0) for r in completed if "num_relevant_chunks" in r
            )
        else:
            avg_recall5 = avg_recall10 = avg_mrr5 = avg_mrr10 = avg_ndcg5 = avg_ndcg10 = 0.0
            avg_chunks = avg_relevant = 0.0

        print(f"""
  ┌─────────────────────────────────────────────────┐
  │               EVALUATION SCORECARD                │
  ├────────────────────────────────┬────────────────┤
  │  Answer Quality                │  Score (0-10)  │
  ├────────────────────────────────┼────────────────┤
  │  Faithfulness                  │     {avg_faith*10:.1f}           │
  │  Answer Relevance              │     {avg_rel*10:.1f}           │
  │  Citation Precision            │     {avg_cite*10:.1f}           │
  ├────────────────────────────────┼────────────────┤
  │  OVERALL (Quality)             │     {overall:.1f}           │
  ├────────────────────────────────┴────────────────┤
  │  Retrieval Metrics (citation-based relevance)        │
  ├────────────────────────────────┬────────────────┤
  │  Recall@5                      │     {avg_recall5*10:.1f}           │
  │  Recall@10                     │     {avg_recall10*10:.1f}           │
  │  MRR@5                         │     {avg_mrr5*10:.1f}           │
  │  nDCG@5                        │     {avg_ndcg5*10:.1f}           │
  │  nDCG@10                       │     {avg_ndcg10*10:.1f}           │
  ├────────────────────────────────┼────────────────┤
  │  Avg chunks retrieved          │     {avg_chunks:5.1f}           │
  │  Avg cited chunks              │     {avg_relevant:5.1f}           │
  └────────────────────────────────┴────────────────┘

  Queries: {len(completed)}/{len(all_results)} completed
  Latency: p50={p50_lat:.0f}ms  p95={p95_lat:.0f}ms
""")

        # Build results payload (persisted via /api/v1/eval/runs, no local file)
        dump = {
            "overall": round(overall, 1),
            "faithfulness_avg": round(avg_faith, 3),
            "relevance_avg": round(avg_rel, 3),
            "citation_precision_avg": round(avg_cite, 3),
            "latency_p50_ms": round(p50_lat, 0),
            "latency_p95_ms": round(p95_lat, 0),
            "retrieval_metrics": {
                "recall_at_5": round(avg_recall5, 3),
                "recall_at_10": round(avg_recall10, 3),
                "mrr_at_5": round(avg_mrr5, 3),
                "ndcg_at_5": round(avg_ndcg5, 3),
                "ndcg_at_10": round(avg_ndcg10, 3),
                "avg_chunks_retrieved": round(avg_chunks, 1),
                "avg_cited_chunks": round(avg_relevant, 1),
            },
            "results": all_results,
        }
        # Strip retrieval_chunk_ids from per-query results (too verbose for JSON)
        for r in dump["results"]:
            r.pop("retrieved_chunk_ids", None)
            r.pop("chunk_relevance_scores", None)

        # Persist run to the backend (best-effort — warn on failure, never fatal)
        if token:
            payload = {
                "judge_provider": judge_provider,
                "judge_model": OPENCODE_ZEN_MODEL if judge_provider == "opencode_zen" else OLLAMA_MODEL,
                "llm_model": os.environ.get("RAG_LLM_MODEL") or None,
                "embedding_model": "nomic-embed-text",
                "retrieval_top_k": 25,
                "mmr_lambda": 0.4,
                "prompt_version": "v2",
                "overall": round(overall, 1),
                "metrics": {
                    "faithfulness": round(avg_faith, 3),
                    "relevance": round(avg_rel, 3),
                    "citation_precision": round(avg_cite, 3),
                    "latency_p50_ms": round(p50_lat, 0),
                    "latency_p95_ms": round(p95_lat, 0),
                    **dump["retrieval_metrics"],
                },
                "results": dump["results"],
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{base_url}/api/v1/eval/runs",
                        json=payload,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                if resp.status_code in (200, 201):
                    run_id = resp.json().get("id", "?")
                    print(f"  Eval run persisted: run_id={run_id}")
                else:
                    print(f"  ⚠  Failed to persist eval run ({resp.status_code}): {resp.text[:200]}")
            except Exception as exc:
                print(f"  ⚠  Failed to persist eval run: {exc}")
        else:
            print("  ⚠  No auth token — skipped persisting eval run. Pass --token to upload.")

        return {
            "overall": overall,
            "faithfulness": avg_faith,
            "relevance": avg_rel,
            "citation_precision": avg_cite,
            "latency_p50": p50_lat,
            "latency_p95": p95_lat,
            "retrieval_metrics": {
                "recall_at_5": avg_recall5,
                "recall_at_10": avg_recall10,
                "mrr_at_5": avg_mrr5,
                "ndcg_at_5": avg_ndcg5,
                "ndcg_at_10": avg_ndcg10,
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG evaluation pipeline")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--report-ids", help="Comma-separated report UUIDs to test against")
    parser.add_argument("--upload", action="store_true", help="Upload test PDFs before eval")
    parser.add_argument("--token", help="Auth token (default: /tmp/token.txt)")
    parser.add_argument(
        "--judge-provider",
        default=os.environ.get("JUDGE_PROVIDER", "ollama"),
        choices=["ollama", "opencode_zen"],
        help="LLM provider for evaluation scoring (default: ollama). Set OPENCODE_ZEN_API_KEY to use opencode_zen.",
    )
    args = parser.parse_args()

    report_ids = args.report_ids.split(",") if args.report_ids else None
    asyncio.run(evaluate(
        base_url=args.base_url,
        report_ids=report_ids,
        upload=args.upload,
        token=args.token or None,
        judge_provider=args.judge_provider,
    ))


if __name__ == "__main__":
    main()
