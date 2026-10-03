from functools import lru_cache
from typing import List, Optional, Union
from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Quản lý cấu hình tập trung (Centralized Settings) cho toàn bộ hệ thống.
    
    Tuân thủ nguyên tắc 12-Factor App (Config in the environment):
    - Đọc các biến từ môi trường hệ thống (System Environment) hoặc file `.env`.
    - Tự động kiểm tra kiểu dữ liệu (Type Validation) bằng Pydantic.
    - Cung cấp giá trị mặc định hợp lý cho môi trường Local Development.
    """

    # --- 1. THÔNG TIN ỨNG DỤNG ---
    PROJECT_NAME: str = "Tour Management & Booking System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True

    # --- 2. CORS (Cross-Origin Resource Sharing) ---
    # Danh sách các domain Frontend được phép gửi request đến API
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",   # Next.js / React dev
        "http://localhost:5173",   # Vite dev
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        # Cho phép người dùng cấu hình dạng chuỗi phân cách bởi dấu phẩy trong .env:
        # BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- 3. BẢO MẬT & JWT (JSON Web Token) ---
    # Trong production, SECRET_KEY bắt buộc phải được sinh ngẫu nhiên mạnh và đặt trong file .env
    SECRET_KEY: str = "insecure_dev_secret_key_change_in_production_at_least_32_bytes_long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24        # 1 ngày
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7                # 7 ngày

    # --- 4. POSTGRESQL DATABASE ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "tour_booking_db"
    
    # Connection Pool settings
    DB_POOL_SIZE: int = 20        # Số lượng kết nối duy trì trong pool
    DB_MAX_OVERFLOW: int = 10     # Số lượng kết nối tối đa có thể mở vượt mức pool khi tải cao
    DB_POOL_TIMEOUT: int = 30     # Thời gian chờ (giây) để mượn kết nối trước khi văng lỗi Timeout

    @computed_field
    @property
    def async_database_url(self) -> str:
        """Chuỗi kết nối bất đồng bộ cho SQLAlchemy AsyncEngine (sử dụng driver asyncpg)"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Chuỗi kết nối đồng bộ phục vụ cho Alembic Migration (sử dụng driver psycopg2)"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- 5. REDIS CACHE & TEMPORARY LOCK ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @computed_field
    @property
    def redis_url(self) -> str:
        """Chuỗi kết nối tới Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # --- 6. CELERY BACKGROUND WORKER ---
    @computed_field
    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @computed_field
    @property
    def celery_result_backend(self) -> str:
        return self.redis_url

    # --- 7. BOOKING ENGINE CONSTRAINTS ---
    BOOKING_HOLD_TIMEOUT_MINUTES: int = 15  # Thời gian giữ chỗ tạm thời trong Redis trước khi hết hạn

    # --- 8. AI & VECTOR EMBEDDING ---
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    VECTOR_DIMENSION: int = 768  # Kích thước vector embedding (phù hợp với text-embedding-004 hoặc Gemini)

    # --- 9. TƯƠNG THÍCH NGƯỢC (BACKWARD COMPATIBILITY) ---
    ADMIN_EMAIL: str = "admin@travelbooking.com"
    ADMIN_PASSWORD: str = "Admin@123456"
    ADMIN_FULL_NAME: str = "System Administrator"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return self.async_database_url

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return self.redis_url

    @property
    def APP_NAME(self) -> str:
        return self.PROJECT_NAME

    @property
    def APP_VERSION(self) -> str:
        return self.VERSION

    @property
    def APP_ENV(self) -> str:
        return self.ENVIRONMENT

    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.SECRET_KEY

    @property
    def JWT_ALGORITHM(self) -> str:
        return self.ALGORITHM

    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def JWT_REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return self.BACKEND_CORS_ORIGINS

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    # --- CẤU HÌNH PYDANTIC SETTINGS ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Bỏ qua các biến thừa trong .env mà không báo lỗi
    )


@lru_cache
def get_settings() -> Settings:
    """
    Tạo Singleton instance cho Settings.
    Sử dụng @lru_cache để đảm bảo file .env chỉ được đọc và validate một lần duy nhất
    khi server khởi động, tránh đọc file đĩa lặp đi lặp lại ở mỗi request.
    """
    return Settings()


# Biến toàn cục tiện lợi để import trực tiếp ở các module khác: from app.core.config import settings
settings: Settings = get_settings()
