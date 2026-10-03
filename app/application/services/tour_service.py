# ============================================================
# Travel Booking System — Service: Tour du lịch (Tour Service)
# ============================================================
# Tầng nghiệp vụ Tour: Tìm kiếm, tạo mới, chỉnh sửa và quản lý vòng đời Tour.
# Không dùng ORM — Tương tác qua TourRepository gọi Stored Procedures PostgreSQL.
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
import asyncpg
from loguru import logger

from app.application.dto.common import PaginatedResponse
from app.application.dto.tour import (
    ActivityResponse,
    ItineraryResponse,
    TourCreate,
    TourListResponse,
    TourResponse,
    TourUpdate,
)
from app.core.exceptions import BadRequestError, NotFoundError
from app.infrastructure.repositories.tour_repository import TourRepository


def _to_tour_list_item(row: dict) -> TourListResponse:
    """Chuyển đổi bản ghi tóm tắt sang TourListResponse DTO."""
    return TourListResponse(
        id=row.get("tour_id") or row.get("id"),
        tour_code=row["tour_code"],
        title=row["title"],
        category=row.get("category"),
        destination=row["destination"],
        base_price_adult=float(row["base_price_adult"]),
        base_price_child=float(row["base_price_child"]),
        max_participants=row["max_participants"],
        available_slots=row["available_slots"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        status=row["status"],
        created_at=row["created_at"],
    )


def _to_tour_detail(tour_dict: dict) -> TourResponse:
    """Chuyển đổi bản ghi chi tiết kèm lịch trình sang TourResponse DTO."""
    itins = []
    for i in tour_dict.get("itineraries", []):
        acts = [
            ActivityResponse(
                id=a["id"],
                time_slot=a.get("time_slot"),
                place_name=a["place_name"],
                description=a.get("description"),
            )
            for a in i.get("activities", [])
        ]
        itins.append(
            ItineraryResponse(
                id=i["id"],
                day_number=i["day_number"],
                title=i["title"],
                activities=acts,
            )
        )

    return TourResponse(
        id=tour_dict.get("tour_id") or tour_dict.get("id"),
        tour_code=tour_dict["tour_code"],
        title=tour_dict["title"],
        description=tour_dict.get("description"),
        category=tour_dict.get("category"),
        destination=tour_dict["destination"],
        base_price_adult=float(tour_dict["base_price_adult"]),
        base_price_child=float(tour_dict["base_price_child"]),
        max_participants=tour_dict["max_participants"],
        available_slots=tour_dict["available_slots"],
        start_date=tour_dict["start_date"],
        end_date=tour_dict["end_date"],
        status=tour_dict["status"],
        created_by=tour_dict.get("created_by"),
        itineraries=itins,
        created_at=tour_dict["created_at"],
        updated_at=tour_dict["updated_at"],
    )


class TourService:
    """Nghiệp vụ quản lý Tour du lịch."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self._repo = TourRepository(conn)

    async def search_tours(
        self,
        *,
        destination: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = "PUBLISHED",  # Mặc định khách chỉ thấy tour đang mở bán
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        start_date_from: Optional[date] = None,
        start_date_to: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[TourListResponse]:
        """Tìm kiếm, lọc danh sách tour với phân trang."""
        skip = (page - 1) * page_size
        rows, total = await self._repo.search_tours(
            destination=destination,
            category=category,
            status=status,
            min_price=min_price,
            max_price=max_price,
            start_date_from=start_date_from,
            start_date_to=start_date_to,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=page_size,
        )

        items = [_to_tour_list_item(r) for r in rows]
        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_tour(self, tour_id: uuid.UUID) -> TourResponse:
        """Lấy chi tiết một tour kèm lịch trình các ngày."""
        tour = await self._repo.get_by_id(tour_id)
        if not tour:
            raise NotFoundError("Tour", tour_id)
        return _to_tour_detail(tour)

    async def create_tour(
        self,
        data: TourCreate,
        created_by: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TourResponse:
        """
        Tạo tour mới và toàn bộ lịch trình, hoạt động đi kèm trong một transaction.
        """
        if data.end_date <= data.start_date:
            raise BadRequestError("Ngày kết thúc tour phải sau ngày khởi hành")

        # 1. Gọi stored procedure tạo Tour
        new_tour = await self._repo.create_tour(
            title=data.title,
            description=data.description or "",
            category=data.category or "Chung",
            destination=data.destination,
            base_price_adult=data.base_price_adult,
            base_price_child=data.base_price_child,
            max_participants=data.max_participants,
            start_date=data.start_date,
            end_date=data.end_date,
            created_by=created_by,
            ip_address=ip_address,
        )

        tour_id = new_tour["tour_id"]

        # 2. Thêm lịch trình từng ngày nếu có
        for itin in data.itineraries:
            saved_itin = await self._repo.add_itinerary(
                tour_id=tour_id,
                day_number=itin.day_number,
                title=itin.title,
            )
            itin_id = saved_itin["itinerary_id"]

            for act in itin.activities:
                await self._repo.add_activity(
                    itinerary_id=itin_id,
                    time_slot=act.time_slot,
                    place_name=act.place_name,
                    description=act.description,
                )

        logger.info("Đã tạo tour mới: {} (Mã: {})", data.title, new_tour.get("tour_code"))
        return await self.get_tour(tour_id)

    async def update_tour(
        self,
        tour_id: uuid.UUID,
        data: TourUpdate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TourResponse:
        """Cập nhật thông tin cơ bản của tour."""
        updated = await self._repo.update_tour(
            tour_id=tour_id,
            title=data.title,
            description=data.description,
            category=data.category,
            destination=data.destination,
            base_price_adult=data.base_price_adult,
            base_price_child=data.base_price_child,
            max_participants=data.max_participants,
            start_date=data.start_date,
            end_date=data.end_date,
            user_id=user_id,
            ip_address=ip_address,
        )
        if not updated:
            raise NotFoundError("Tour", tour_id)

        return await self.get_tour(tour_id)

    async def publish_tour(
        self,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TourResponse:
        """Xuất bản tour (DRAFT -> PUBLISHED)."""
        await self._repo.publish_tour(tour_id, user_id, ip_address)
        return await self.get_tour(tour_id)

    async def close_tour(
        self,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TourResponse:
        """Đóng tour (PUBLISHED -> ARCHIVED)."""
        await self._repo.close_tour(tour_id, user_id, ip_address)
        return await self.get_tour(tour_id)

    async def cancel_tour(
        self,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> TourResponse:
        """Hủy tour (-> CANCELLED)."""
        await self._repo.cancel_tour(tour_id, user_id, ip_address)
        return await self.get_tour(tour_id)
