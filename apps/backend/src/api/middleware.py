"""Custom middleware registration for the FastAPI application.

Two layers beyond the timing header:

* ``SecurityHeadersMiddleware`` — sets hardening response headers on every
  reply (nosniff, frame denial, referrer policy, HSTS over HTTPS).
* ``CrossSiteGuardMiddleware`` — rejects cross-site state-changing requests,
  the CSRF defense-in-depth layer on top of the SameSite=Lax auth cookie.
"""

import logging
import time
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Methods that mutate state and therefore need CSRF protection.
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds an X-Process-Time header with the request duration in seconds."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply hardening headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # HSTS only when the client is actually on HTTPS — honours the
        # reverse proxy's X-Forwarded-Proto.
        if request.headers.get("x-forwarded-proto", request.url.scheme) == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
        return response


class CrossSiteGuardMiddleware(BaseHTTPMiddleware):
    """Block cross-site state-changing requests (CSRF defense-in-depth).

    A browser sending a mutating request includes ``Sec-Fetch-Site``; a value
    of ``cross-site`` is rejected before it reaches a handler. When that
    header is absent but ``Origin`` is present, the origin must be same-host
    or in ``CORS_ORIGINS``. Clients that send neither header (curl, the eval
    script, server-to-server) pass through untouched — the Bearer-token path
    is unaffected.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method in _MUTATING_METHODS and self._is_cross_site(request):
            logger.warning("Blocked cross-site %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=403,
                content={"detail": "Cross-site request blocked"},
            )
        return await call_next(request)

    @staticmethod
    def _is_cross_site(request: Request) -> bool:
        site = request.headers.get("sec-fetch-site")
        origin = request.headers.get("origin")

        if site is not None:
            # same-origin / same-site / none are all fine; only cross-site is hostile.
            return site == "cross-site"

        if origin is None:
            # Non-browser client — no CSRF context.
            return False

        allowed = set(get_settings().CORS_ORIGINS)
        host = request.headers.get("host", "")
        return not (origin in allowed or urlsplit(origin).netloc == host)


def add_middleware(app: FastAPI) -> None:
    """Register all custom middleware on the application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(TimingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CrossSiteGuardMiddleware)
    logger.debug("Custom middleware registered")
