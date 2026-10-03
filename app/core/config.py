# ============================================================
# Travel Booking System — Cấu hình tập trung (Config)
# ============================================================
# Đọc biến môi trường từ file .env hoặc giá trị mặc định.
# Tất cả cấu hình hệ thống nằm ở đây, các module khác chỉ cần
# import settings là dùng được.
# ============================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Cấu hình tập trung cho toàn bộ hệ thống.

    Cách hoạt động:
    - Pydantic tự động đọc giá trị từ file .env
    - Nếu .env không có, dùng giá trị mặc định bên dưới
    - Tự động kiểm tra kiểu dữ liệu (ví dụ: PORT phải là số)
    """

    # --- Thông tin ứng dụng ---
    PROJECT_NAME: str = "Travel Booking System"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"    # development / production
    DEBUG: bool = True

    # --- Cấu hình API ---
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Cấu hình PostgreSQL (Database local) ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 8888           # Port PostgreSQL của bạn
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123456"   # Mật khẩu PostgreSQL của bạn
    POSTGRES_DB: str = "tour_booking_db"

    # Connection Pool: Số kết nối giữ sẵn để tái sử dụng (tránh mở/đóng liên tục)
    DB_POOL_MIN: int = 2       # Số kết nối tối thiểu luôn sẵn sàng
    DB_POOL_MAX: int = 10      # Số kết nối tối đa khi tải cao

    # --- Cấu hình JWT (Token xác thực) ---
    # SECRET_KEY dùng để ký và xác minh token. Trong production phải đổi thành chuỗi ngẫu nhiên dài.
    SECRET_KEY: str = "thay-doi-key-nay-trong-production-it-nhat-32-ky-tu-nhe"
    JWT_ALGORITHM: str = "HS256"                    # Thuật toán mã hóa token
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24      # Token hết hạn sau 24 giờ
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7              # Refresh token hết hạn sau 7 ngày

    # --- Cấu hình CORS (cho phép Frontend gọi API) ---
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"

    # --- Tài khoản Admin mặc định ---
    ADMIN_EMAIL: str = "admin@travelbooking.com"
    ADMIN_PASSWORD: str = "Admin@123456"

    @property
    def database_url(self) -> str:
        """Chuỗi kết nối PostgreSQL cho asyncpg (không qua ORM)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Chuyển chuỗi CORS thành danh sách."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # --- Cấu hình Pydantic ---
    model_config = SettingsConfigDict(
        env_file=".env",            # Đọc từ file .env
        env_file_encoding="utf-8",
        case_sensitive=True,        # Phân biệt HOA/thường
        extra="ignore",             # Bỏ qua biến thừa trong .env
    )


# Tạo 1 instance duy nhất dùng cho toàn bộ ứng dụng (Singleton Pattern)
settings = Settings()
