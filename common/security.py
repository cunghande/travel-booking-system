# khai báo thư viện 
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from common.exceptions import ForbiddenError, UnauthorizedError

# đọc các biến từ file .env
SECRET_KEY = os.getenv("SECRET_KEY", "b9c45e8f2a1d7c3b8e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
# cấu hình hàm băm mật khẩu bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# khởi tạo http request header 
security_bearer = HTTPBearer(auto_error=False)

# khởi tạo hàm băm, băm mật khẩu người dùng trước khi cho vào sql
def hash_password(password: str):
    return pwd_context.hash(password)

# hàm kiểm tra password có khớp với hash trong database không
def verify_password(plain_password: str, hashed_password: str):
    # nếu không khớp => False, nếu khớp => True
    return pwd_context.verify(plain_password, hashed_password)

# hàm tạo access token
def create_access_token(user_id: str, role: str, email: str):
    # sinh access token mặc định trong 60 phút
    expire =datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role":str(role),
        "email":str(email),
        "type":"access",
        "exp": expire,
    }
    # trộn phần thông tin payload với SECRET_KEY để tạo ra chuỗi JWT
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

# hàm refresh token trong 7 ngày
def create_refresh_token(user_id: str) -> str:
    """Sinh Refresh Token có thời hạn dài (mặc định 7 ngày)."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# hàm giải mã và kiểm tra JWT token
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise UnauthorizedError("Token không hợp lệ hoặc hết hạn")

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
):
    # Lấy thông tin từ API Gateway
    header_user_id = request.headers.get("X-User-ID")
    header_role = request.headers.get("X-User-Role")
    header_email = request.headers.get("X-User-Email")
    if header_user_id and header_role:
        return {
            "user_id": header_user_id,
            "role": header_role,
            "email": header_email or "",
        }
    if not credentials:
        raise UnauthorizedError("Yêu cầu gửi kèm Bearer Token để xác thực")
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email", "")
    if not user_id or not role:
        raise UnauthorizedError("Token thiếu thông tin user_id hoặc role")
    return {
        "user_id": user_id,
        "role": role,
        "email": email,
    }
async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Kiểm tra người dùng hiện tại có vai trò ADMIN hay không.
    Nếu không phải ADMIN -> Bắn ra lỗi HTTP 403 Forbidden.
    """
    if current_user.get("role") != "ADMIN":
        raise ForbiddenError("Thao tác này chỉ dành cho Quản trị viên (ADMIN)")
    return current_user
