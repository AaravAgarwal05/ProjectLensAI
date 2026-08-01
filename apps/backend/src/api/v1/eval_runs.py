"""REST API endpoints for persisted evaluation runs.

Allows authenticated users to store RAG evaluation results and
retrieve them for comparison across prompt/retrieval configs.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai_core.eval.database import EvalRunModel
from src.api.dependencies import get_current_user, get_db
from src.database.models.user import User

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class EvalRunCreate(BaseModel):
    """Body for creating an evaluation run."""

    judge_provider: str
    judge_model: str
    llm_model: str | None = None
    embedding_model: str | None = None
    retrieval_top_k: int | None = None
    mmr_lambda: float | None = None
    prompt_version: str | None = None
    overall: float
    metrics: dict[str, Any] = Field(default_factory=dict)
    results: list[dict[str, Any]] = Field(default_factory=list)


class EvalRunOut(BaseModel):
    """Evaluation run summary (list view)."""

    id: str
    created_at: str
    overall: float
    judge_provider: str
    judge_model: str
    llm_model: str | None = None
    embedding_model: str | None = None
    retrieval_top_k: int | None = None
    mmr_lambda: float | None = None
    prompt_version: str | None = None


class EvalRunDetail(EvalRunOut):
    """Full evaluation run including metrics and per-query results."""

    metrics: dict[str, Any] = Field(default_factory=dict)
    results: list[dict[str, Any]] = Field(default_factory=list)


def _model_to_out(model: EvalRunModel) -> EvalRunOut:
    return EvalRunOut(
        id=model.id,
        created_at=model.created_at.isoformat() if model.created_at else "",
        overall=model.overall,
        judge_provider=model.judge_provider,
        judge_model=model.judge_model,
        llm_model=model.llm_model,
        embedding_model=model.embedding_model,
        retrieval_top_k=model.retrieval_top_k,
        mmr_lambda=model.mmr_lambda,
        prompt_version=model.prompt_version,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/runs", response_model=EvalRunOut, status_code=status.HTTP_201_CREATED)
async def create_eval_run(
    body: EvalRunCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EvalRunOut:
    """Store an evaluation run and return its ID."""
    run = EvalRunModel(
        judge_provider=body.judge_provider,
        judge_model=body.judge_model,
        llm_model=body.llm_model,
        embedding_model=body.embedding_model,
        retrieval_top_k=body.retrieval_top_k,
        mmr_lambda=body.mmr_lambda,
        prompt_version=body.prompt_version,
        overall=body.overall,
        metrics=body.metrics,
        results=body.results,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return _model_to_out(run)


@router.get("/runs", response_model=list[EvalRunOut])
async def list_eval_runs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[EvalRunOut]:
    """List evaluation runs, newest first."""
    result = await db.execute(
        select(EvalRunModel)
        .order_by(EvalRunModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return [_model_to_out(r) for r in result.scalars().all()]


@router.get("/runs/{run_id}", response_model=EvalRunDetail)
async def get_eval_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EvalRunDetail:
    """Return a single evaluation run with its full metrics and results."""
    run = await db.get(EvalRunModel, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Eval run '{run_id}' not found")
    out = _model_to_out(run).model_dump()
    out["metrics"] = run.metrics or {}
    out["results"] = run.results or []
    return EvalRunDetail(**out)
