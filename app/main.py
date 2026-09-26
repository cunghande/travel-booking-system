# ============================================================
# Travel Booking System — FastAPI Application
# ============================================================

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.infrastructure.redis.client import close_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    # --- Startup ---
    setup_logging()
    logger.info(
        "Application starting: {} v{} | env={}",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    yield
    # --- Shutdown ---
    await close_redis_pool()
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """Application factory."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Tour Management & Booking System with AI Integration",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # --- Middleware ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception Handlers ---
    @application.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: {}", str(exc))
        # Never expose stack trace to client in production
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            },
        )

    # --- Routes ---
    application.include_router(v1_router)

    # --- Static Files & Frontend ---
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        application.mount("/static", StaticFiles(directory=static_dir), name="static")

    @application.get("/", tags=["Frontend"])
    async def serve_frontend():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {
            "message": "Wanderlust Travel API is running.",
            "docs": "/docs",
        }

    @application.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
        }

    return application


app = create_app()
