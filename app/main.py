# ============================================================
# Travel Booking System — FastAPI Application
# ============================================================
# Tích hợp toàn diện: Middleware Pipeline + Clean Architecture
# Phục vụ API RESTful v1 + Giao diện Web (Frontend UI)
# Sử dụng kết nối PostgreSQL local qua Connection Pool asyncpg thuần
# ============================================================

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import close_db_pool, init_db_pool
from app.core.exceptions import AppException
from app.middleware.logging import LoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.timing import TimingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Quản lý vòng đời (Lifespan) của ứng dụng FastAPI.
    - Code trước yield: Thực thi khi Server khởi động (Startup) -> Tạo Pool asyncpg.
    - Code sau yield: Thực thi khi Server tắt (Shutdown) -> Đóng Pool kết nối.
    """
    print(f"[LIFESPAN] 🚀 Ứng dụng '{settings.PROJECT_NAME}' (v{settings.VERSION}) đang khởi động...")
    print(f"[LIFESPAN] 🌐 Môi trường: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")

    # Khởi tạo connection pool tới PostgreSQL local
    try:
        await init_db_pool()
        print("[LIFESPAN] ✅ Đã kết nối cơ sở dữ liệu PostgreSQL local thành công.")
    except Exception as e:
        print(f"[LIFESPAN] ⚠️ Chưa thể kết nối PostgreSQL ({e}). Hãy đảm bảo dịch vụ PostgreSQL đang chạy.")

    yield

    print("[LIFESPAN] 🛑 Ứng dụng đang tắt: Thu hồi và dọn dẹp tài nguyên...")
    await close_db_pool()


# Khởi tạo FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống Quản lý & Đặt Tour Du lịch Tích hợp AI",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ==============================================================================
# ĐĂNG KÝ CHUỖI MIDDLEWARE (MIDDLEWARE PIPELINE)
# ==============================================================================

# 1. CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 2. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Timing Middleware
app.add_middleware(TimingMiddleware)

# 4. Logging Middleware
app.add_middleware(LoggingMiddleware)

# 5. Request ID Middleware
app.add_middleware(RequestIdMiddleware)


# ==============================================================================
# XỬ LÝ LỖI TOÀN CỤC (GLOBAL EXCEPTION HANDLERS)
# ==============================================================================

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Xử lý các lỗi nghiệp vụ chuẩn hóa (AppException)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


# ==============================================================================
# ROUTERS & GIAO DIỆN WEB
# ==============================================================================

# 1. API V1 Routes
app.include_router(v1_router)

# 2. Static Files & Frontend UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get(
    "/",
    tags=["Frontend & Root"],
    summary="Trang chủ giao diện người dùng",
)
async def serve_frontend():
    """Phục vụ giao diện web trực quan của hệ thống."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return {
        "success": True,
        "message": f"Chào mừng đến với {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["Health Check"],
    summary="Kiểm tra sức khỏe hệ thống",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "tour-booking-api",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }
