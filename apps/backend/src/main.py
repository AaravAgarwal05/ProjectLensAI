"""ProjectLens AI — FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exceptions import register_exception_handlers
from src.api.middleware import add_middleware
from src.api.rate_limiter import SlowAPIMiddleware, _rate_limit_exceeded_handler, limiter
from src.api.v1.router import api_router
from src.config.logging import configure_logging
from src.config.settings import AppSettings, get_settings
from src.core.bootstrap import bootstrap_app

logger = logging.getLogger(__name__)


def _init_sentry(settings: AppSettings) -> None:
    """Initialise Sentry error reporting when a DSN is configured.

    Imported lazily so a missing sentry-sdk can never crash the app — the
    dependency is optional at runtime.
    """
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENV,
            traces_sample_rate=0.1,
        )
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed — skipping.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: runs startup and shutdown logic."""
    configure_logging()
    _init_sentry(get_settings())
    await bootstrap_app(app)
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    add_middleware(app)

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(429, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)  # noqa: E402

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
