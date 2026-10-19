import uuid
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
import aiomysql
from common.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from services.auth_service.database import get_db
from services.auth_service.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

# Khởi tạo Router cho Auth Service
router = APIRouter(prefix="/auth", tags=["Xác thực & Tài khoản"])

# xây dựng api đăng ký tài khoản (POST /auth/register)
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới"
)
async def register(
    data: RegisterRequest,
    conn: aiomysql.Connection =Depends(get_db),
):
    # tạo id cho người dùng
    user_id= str(uuid.uuid4())
    hashed_pwd =hash_password(data.password)

    async with conn.cursor() as cur:
        try:
            # gọi procedure để tạo user
            await cur.execute(
                "CALL sp_register_user(%s, %s, %s, %s, %s)",
                (user_id, data.email, hashed_pwd, data.full_name, data.phone_number),
            )
        except Exception as e:
            err_msg= str(e)
            if "Email đã tồn tại" in err_msg or "1062" in err_msg or "45000" in err_msg:
                raise ConflictError("Email đã tồn tại trong hệ thống")
            raise BadRequestError(f"Đăng ký thất bị:{err_msg}")
    
    # tạo access token và refresh token cho tài khoản mới
    access_token = create_access_token(user_id=user_id, role="CUSTOMER",email=data.email)
    refresh_token = create_refresh_token(user_id= user_id)

    user_resp = UserResponse(
        id = user_id,
        email = data.email,
        full_name = data.full_name,
        phone_number =data.phone_number,
        role = "CUSTOMER",
        is_active = True,
    )

    return TokenResponse(
        access_token = access_token,
        refresh_token = refresh_token,
        user = user_resp,
    )
            

# xây dựng api đăng nhập (POST /auth/login)
@router.post(
    "/login",
    response_model = TokenResponse,
    summary = " Đăng nhập tài khoản lấy JWT token",
)
async def login(
    data: LoginRequest,
    conn: aiomysql.Connection = Depends(get_db),
):
    # Kiểm tra tài khoản đã tồn tại chưa
    async with conn.cursor() as cur:
        await cur.execute("CALL sp_get_user_by_email(%s)", (data.email,))
        user = await cur.fetchone()
    
    # nếu không tìm thấy email và mật khẩu khớp 
    if not user:
        raise UnauthorizedError("Email hoặc mật khẩu không chính xác")

    if not verify_password(data.password, user["hashed_password"]):
        raise UnauthorizedError("Email hoặc mật khẩu không chính xác")
    
    # Kiểm tra xem tài khoản có bị khóa không
    if not user["is_active"]:
        raise ForbiddenError("Tài khoản đã bị khóa")
    

    # cấp token mới 
    access_token = create_access_token(
        user_id = user["id"],
        role = user["role"],
        email = user["email"],
    )
    refresh_token = create_refresh_token(user_id = user["id"]) 

    user_resp = UserResponse(
        id = user["id"],
        email = user["email"],
        full_name = user["full_name"],
        phone_number = user.get("phone_number"),
        role = user["role"],
        is_active =bool(user["is_active"]),
    )

    return TokenResponse(
        access_token = access_token,
        refresh_token = refresh_token,
        user = user_resp,
    )

# api làm mới token
@router.post(
    "/refresh",
    response_model = TokenResponse,
    summary = "Cấp lại Access Token khi hết hạn"
)
async def refresh_token(
    data: RefreshTokenRequest,
    conn: aiomysql.Connection = Depends(get_db),
):
    payload =decode_token(data.refresh_token)
    if payload.get("type") !="refresh":
        raise UnauthorizedError("Token cung cấp không phải Refresh hợp lệ")
    
    user_id = payload.get("sub")

    async with conn.cursor() as cur:
            await cur.execute("CALL sp_get_user_by_id(%s)", (user_id,))
            user = await cur.fetchone()

    if not user or not user.get("is_active"):
        raise UnauthorizedError("tài khoản không tồn tại hoặc bị khóa")
    
    new_access_token = create_access_token(
        user_id =user["id"],
        role =user["role"],
        email =user["email"],
    )
    new_refresh_token =create_refresh_token(user_id =user["id"])

    user_resp = UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        phone_number=user.get("phone_number"),
        role=user["role"],
        is_active=bool(user["is_active"]),
    )

    return TokenResponse(
        access_token =new_access_token,
        refresh_token =new_refresh_token,
        user =user_resp,
    )

# xây dựng api hiển thị thông tin tài khoản (GET /auth/me)

@router.get(
    "/me",
    response_model = UserResponse,
    summary ="Xem thông tin tài khoản đăng nhập",
)

async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_db),
):

    user_id = current_user["user_id"]
    async with conn.cursor() as cur:
        await cur.execute("CALL sp_get_user_by_id(%s)", (user_id,))
        user = await cur.fetchone()
    
    if not user:
        raise NotFoundError("Người dùng",user_id)
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        phone_number=user.get("phone_number"),
        role=user["role"],
        is_active=bool(user["is_active"]),
    )
