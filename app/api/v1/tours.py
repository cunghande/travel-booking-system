# ============================================================
# Travel Booking System — API Router: Tour du lịch (Tours)
# ============================================================
# Các endpoints: Tìm kiếm lọc tour, xem chi tiết, tạo mới, chỉnh sửa, đổi trạng thái.
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Optional
import uuid
from fastapi import APIRouter, Query, Request

from app.application.dto.common import PaginatedResponse
from app.application.dto.tour import (
    TourCreate,
    TourListResponse,
    TourResponse,
    TourUpdate,
)
from app.application.services.tour_service import TourService
from app.core.dependencies import DBConn, StaffUser, get_client_ip

router = APIRouter(prefix="/tours", tags=["Quản lý Tour du lịch"])


@router.get(
    "",
    response_model=PaginatedResponse[TourListResponse],
    summary="Tìm kiếm và lọc danh sách Tour",
    description="Công khai cho khách hàng. Mặc định chỉ hiển thị tour đang mở bán (PUBLISHED).",
)
async def list_tours(
    conn: DBConn,
    destination: Optional[str] = Query(None, description="Lọc theo điểm đến (Đà Nẵng, Phú Quốc...)"),
    category: Optional[str] = Query(None, description="Lọc theo danh mục (Biển, Núi...)"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Giá vé tối thiểu"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Giá vé tối đa"),
    start_date_from: Optional[date] = Query(None, description="Khởi hành từ ngày"),
    start_date_to: Optional[date] = Query(None, description="Khởi hành trước ngày"),
    search: Optional[str] = Query(None, description="Từ khóa tìm kiếm theo tên hoặc mô tả tour"),
    sort_by: str = Query("created_at", description="Sắp xếp theo: created_at, base_price_adult, start_date"),
    sort_order: str = Query("desc", description="Thứ tự: asc, desc"),
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số tour mỗi trang"),
) -> PaginatedResponse[TourListResponse]:
    service = TourService(conn)
    return await service.search_tours(
        destination=destination,
        category=category,
        status="PUBLISHED",
        min_price=min_price,
        max_price=max_price,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/manage",
    response_model=PaginatedResponse[TourListResponse],
    summary="Quản lý toàn bộ Tour (Staff / Admin)",
    description="Nhân viên hoặc Admin xem tất cả các tour kể cả DRAFT, ARCHIVED, CANCELLED.",
)
async def manage_tours(
    conn: DBConn,
    staff: StaffUser,
    destination: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Lọc trạng thái: DRAFT, PUBLISHED, ARCHIVED, CANCELLED"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[TourListResponse]:
    service = TourService(conn)
    return await service.search_tours(
        destination=destination,
        category=category,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{tour_id}",
    response_model=TourResponse,
    summary="Xem chi tiết Tour và Lịch trình",
    description="Lấy thông tin tour kèm lịch trình từng ngày và các hoạt động chi tiết.",
)
async def get_tour(
    tour_id: uuid.UUID,
    conn: DBConn,
) -> TourResponse:
    service = TourService(conn)
    return await service.get_tour(tour_id)


@router.post(
    "",
    response_model=TourResponse,
    status_code=201,
    summary="Tạo Tour mới (Staff / Admin)",
    description="Tạo tour mới kèm lịch trình và các hoạt động từng ngày.",
)
async def create_tour(
    data: TourCreate,
    conn: DBConn,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(conn)
    return await service.create_tour(
        data,
        created_by=staff["id"],
        ip_address=get_client_ip(request),
    )


@router.put(
    "/{tour_id}",
    response_model=TourResponse,
    summary="Cập nhật Tour (Staff / Admin)",
    description="Chỉnh sửa thông tin cơ bản của tour (DRAFT hoặc PUBLISHED).",
)
async def update_tour(
    tour_id: uuid.UUID,
    data: TourUpdate,
    conn: DBConn,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(conn)
    return await service.update_tour(
        tour_id,
        data,
        user_id=staff["id"],
        ip_address=get_client_ip(request),
    )


@router.post(
    "/{tour_id}/publish",
    response_model=TourResponse,
    summary="Xuất bản Tour (Staff / Admin)",
    description="Chuyển trạng thái tour từ DRAFT sang PUBLISHED để khách hàng có thể đặt chỗ.",
)
async def publish_tour(
    tour_id: uuid.UUID,
    conn: DBConn,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(conn)
    return await service.publish_tour(
        tour_id,
        user_id=staff["id"],
        ip_address=get_client_ip(request),
    )


@router.post(
    "/{tour_id}/close",
    response_model=TourResponse,
    summary="Đóng Tour (Staff / Admin)",
    description="Chuyển trạng thái tour từ PUBLISHED sang ARCHIVED khi tour kết thúc.",
)
async def close_tour(
    tour_id: uuid.UUID,
    conn: DBConn,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(conn)
    return await service.close_tour(
        tour_id,
        user_id=staff["id"],
        ip_address=get_client_ip(request),
    )


@router.post(
    "/{tour_id}/cancel",
    response_model=TourResponse,
    summary="Hủy Tour (Staff / Admin)",
    description="Hủy tour và tự động hủy các booking chưa hoàn tất.",
)
async def cancel_tour(
    tour_id: uuid.UUID,
    conn: DBConn,
    request: Request,
    staff: StaffUser,
) -> TourResponse:
    service = TourService(conn)
    return await service.cancel_tour(
        tour_id,
        user_id=staff["id"],
        ip_address=get_client_ip(request),
    )
