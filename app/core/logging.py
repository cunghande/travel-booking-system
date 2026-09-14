# ============================================================
# Travel Booking System — Logging Configuration
# ============================================================
# Structured logging with Loguru.
# Sensitive data (secrets, tokens, payment info) is never logged.
# ============================================================

from __future__ import annotations

import sys

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Configure Loguru for the application."""
    # Remove default handler
    logger.remove()

    # Console handler
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
        enqueue=True,  # Thread-safe
    )

    # File handler (production)
    if settings.is_production:
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation="00:00",  # Rotate at midnight
            retention="30 days",
            compression="gz",
            enqueue=True,
        )

    logger.info(
        "Logging initialized | env={} | level={}",
        settings.APP_ENV,
        log_level,
    )
