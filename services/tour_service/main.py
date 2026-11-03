# khai báo thư viện
import os 
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from common.exceptions import AppException
from services.tour_service.database import init_db_pool, close_db_pool
from services.tour_service.router import router as tour_router


# quản lý vòng đời ứng dụng
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()

# khởi tạo FastAPI app
app = FastAPI(
    title="Travel Booking - Tour Service",
    description="Microservice quản lý Tour du lịch, lịch trình và hoạt động",
    version="1.0.0",
    lifespan=lifespan,
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# xử lý ngoại lệ
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Da xay ra loi may chu noi bo",
            "details": {"error": str(exc)},
        },
    )


app.include_router(tour_router)
# Health check
@app.get("/health", tags=["He thong"])
async def health_check():
    return {
        "service": "tour_service",
        "status": "healthy",
        "port": 8002,
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.tour_service.main:app", host="0.0.0.0", port=8002, reload=True)
