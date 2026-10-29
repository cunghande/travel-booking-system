# khai báo thư viện 
import sys
from pathlib import Path
# Thêm thư mục gốc vào danh sách tìm kiếm của Python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv


# 1 tải biến môi trường
load_dotenv()

from common.exceptions import AppException
from services.auth_service.database import init_db_pool, close_db_pool
from services.auth_service.router import router as auth_router

# 2 quản lý vòng đời ứng dụng mở và đóng sql tự động
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()

#3 khởi tạo Fastapi app
app = FastAPI(
    title = "Travel Booking - Auth Service",
    description="Microservice quản lý xác thực và phân quyền người dùng",
    version = "1.0.0",
    lifespan=lifespan,
)

# 4 cấu hình CORS để cho phép Fronend gọi APi không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5 Xử lý ngoại lệ chuẩn hóa 
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code = exc.status_code,
        content = exc.detail,
    )

# 6 xử lý lỗi không lường được
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        content ={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Đã xảy ra lỗi máy chủ nội bộ",
            "details": {"error": str(exc)},
        },
    )

# 7 gắn router xác thực vào app
app.include_router(auth_router)

# 8 Endpoint kiểm tra trạng thái Service
@app.get("/health", tags = ["Hệ thống"])
async def health_check():
    return {
        "service": "auth_service",
        "status": "healthy",
        "port": 8001,
    }

# 9. Điểm chạy trực tiếp file bằng Python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.auth_service.main:app",
    host="0.0.0.0", port=8001, reload=True)



