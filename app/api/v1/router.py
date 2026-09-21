# ============================================================
# Travel Booking System — V1 Router
# ============================================================

from fastapi import APIRouter

from app.api.v1 import auth, tours, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(tours.router)

