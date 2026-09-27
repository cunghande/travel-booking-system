# ============================================================
# Travel Booking System — Core Middlewares
# ============================================================
# Essential production-grade HTTP middlewares:
# 1. Request ID (Correlation ID) & Request State
# 2. Performance Timing & Request Logging
# 3. Security Headers (OWASP)
# 4. Cross-Origin Resource Sharing (CORS)
# ============================================================

from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts or generates a unique correlation ID (X-Request-ID).
    2. Attaches request_id to request.state.
    3. Measures request execution time (X-Process-Time).
    4. Logs structured HTTP request/response metrics with Loguru.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Determine client IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "[{}] {} {} -> FAILED ({:.2f}ms) | Client: {} | Error: {}",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                client_ip,
                str(exc),
            )
            raise exc

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Append correlation ID and process time to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        # Structured log output based on status code and duration
        log_message = "[{}] {} {} -> {} ({:.2f}ms) | Client: {}"
        log_args = (
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_ip,
        )

        if response.status_code >= 500:
            logger.error(log_message, *log_args)
        elif response.status_code >= 400:
            logger.warning(log_message, *log_args)
        elif duration_ms > 1000:
            logger.warning(log_message + " [SLOW REQUEST]", *log_args)
        else:
            logger.info(log_message, *log_args)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds OWASP-recommended security headers to all responses.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Anti-MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Anti-Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # XSS Protection for legacy browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Enforce HTTPS via HSTS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


def register_middlewares(application: FastAPI) -> None:
    """
    Register core middlewares to the FastAPI application.
    
    Starlette middleware execution order (LIFO for requests, FIFO for responses):
    1. CORS (innermost)
    2. SecurityHeadersMiddleware
    3. RequestLoggingMiddleware (outermost)
    """
    # 1. CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Security Headers
    application.add_middleware(SecurityHeadersMiddleware)

    # 3. Request Logging & Correlation ID
    application.add_middleware(RequestLoggingMiddleware)
