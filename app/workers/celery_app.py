# ============================================================
# Travel Booking System — Celery Application (Placeholder)
# ============================================================
# Will be fully configured in Sprint 2+ for:
# - PDF voucher generation
# - Email sending
# - Vector re-indexing
# - Booking expiration cleanup
# ============================================================

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "travel_booking",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in workers/tasks/
celery_app.autodiscover_tasks(["app.workers.tasks"])
