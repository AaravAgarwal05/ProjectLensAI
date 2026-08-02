"""Application bootstrap — runs once at startup."""

import logging

from fastapi import FastAPI

from src.ai_core.llm.providers.fallback import FallbackLLMProvider
from src.ai_core.llm.registry import default_llm_registry
from src.config.logging import configure_logging
from src.config.settings import get_settings
from src.database.session import init_db
from src.infra.redis import close_redis, get_redis

logger = logging.getLogger(__name__)


async def bootstrap_app(app: FastAPI) -> None:
    """Initialize all application services at startup.

    Performs:
        - Logging configuration
        - Database engine initialisation
        - LLM provider registration
        - ChromaDB client initialisation
        - Startup sanity checks

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    configure_logging()

    logger.info(
        "Starting %s v%s in %s mode",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.environment,
    )

    try:
        await init_db(settings.DATABASE_URL)
        logger.info("Database engine initialised successfully")
    except Exception as exc:
        logger.warning("Database initialisation failed: %s. App will run without DB.", exc)

    # ------------------------------------------------------------------
    # Redis client
    # ------------------------------------------------------------------
    try:
        await get_redis()
        logger.info("Redis client initialised successfully")
    except Exception as exc:
        logger.warning("Redis initialisation failed: %s. App will run without Redis.", exc)

    # ------------------------------------------------------------------
    # LLM provider registration
    # ------------------------------------------------------------------
    _registry = default_llm_registry()
    _registry.register("fallback", FallbackLLMProvider)
    logger.info("Registered LLM providers: %s", _registry.list_names())
    # Attach to app state for downstream use
    app.state.llm_registry = _registry

    # ------------------------------------------------------------------
    # ChromaDB client (singleton, reused across requests)
    # ------------------------------------------------------------------
    try:
        import chromadb

        chroma_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        # Warm the connection with a heartbeat call
        heartbeat = chroma_client.heartbeat()
        app.state.chroma_client = chroma_client
        logger.info("ChromaDB client initialised (heartbeat: %s)", heartbeat)
    except Exception as exc:
        logger.warning("ChromaDB initialisation failed: %s. Vector search will be unavailable.", exc)
        app.state.chroma_client = None

    # ------------------------------------------------------------------
    # Embedding provider warmup
    # ------------------------------------------------------------------
    try:
        from src.ai_core.embedding.factory import build_embedding_provider

        embedder = build_embedding_provider()
        # Probe dimensions and warm the provider
        dims = await embedder.embed("warmup")
        app.state.embedding_provider = embedder
        logger.info("Embedding provider initialised (dims: %d)", len(dims))
    except Exception as exc:
        logger.warning("Embedding provider warmup failed: %s", exc)
        app.state.embedding_provider = None

    logger.info("Startup complete — ready to accept requests")


async def shutdown_app() -> None:
    """Clean up application resources at shutdown."""
    try:
        await close_redis()
    except Exception as exc:
        logger.warning("Redis shutdown error: %s", exc)
