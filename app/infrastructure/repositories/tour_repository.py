# ============================================================
# Travel Booking System — Repository: Tour du lịch (Tour Repository)
# ============================================================
# Tầng truy xuất dữ liệu Tour qua asyncpg và Stored Procedures.
# Không dùng ORM — Gọi trực tiếp các hàm SQL thuần trong PostgreSQL.
# ============================================================

from datetime import date, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import uuid
import asyncpg


class TourRepository:
    """
    Repository quản lý dữ liệu Tour du lịch, Lịch trình (Itinerary) và Hoạt động (Activity).
    Tất cả dữ liệu được lấy hoặc ghi thông qua Stored Functions trong PostgreSQL.
    """

    def __init__(self, conn: asyncpg.Connection):
        """
        Khởi tạo repository với kết nối asyncpg.
        conn được inject tự động từ get_db dependency.
        """
        self._conn = conn

    async def search_tours(
        self,
        destination: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        start_date_from: Optional[date] = None,
        start_date_to: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Tìm kiếm và lọc danh sách tour có phân trang.
        Gọi function: fn_tim_kiem_tour(...)
        """
        sql = """
            SELECT * FROM fn_tim_kiem_tour(
                p_destination := $1,
                p_category := $2,
                p_status := $3,
                p_min_price := $4,
                p_max_price := $5,
                p_start_date_from := $6,
                p_start_date_to := $7,
                p_search := $8,
                p_sort_by := $9,
                p_sort_order := $10,
                p_skip := $11,
                p_limit := $12
            );
        """
        rows = await self._conn.fetch(
            sql,
            destination,
            category,
            status,
            min_price,
            max_price,
            start_date_from,
            start_date_to,
            search,
            sort_by,
            sort_order,
            skip,
            limit,
        )

        if not rows:
            return [], 0

        items = [dict(r) for r in rows]
        total = items[0]["total_count"] if items else 0
        return items, total

    async def get_by_id(self, tour_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết một tour (kèm lịch trình & hoạt động).
        Gọi:
          1. fn_lay_chi_tiet_tour(p_tour_id)
          2. fn_lay_lich_trinh_tour(p_tour_id)
        """
        tour_sql = "SELECT * FROM fn_lay_chi_tiet_tour($1);"
        tour_row = await self._conn.fetchrow(tour_sql, tour_id)
        if not tour_row:
            return None

        tour_dict = dict(tour_row)

        # Lấy lịch trình chi tiết
        itinerary_sql = "SELECT * FROM fn_lay_lich_trinh_tour($1);"
        itin_rows = await self._conn.fetch(itinerary_sql, tour_id)

        # Gom nhóm các hoạt động theo ngày (itinerary)
        itineraries_map: Dict[uuid.UUID, Dict[str, Any]] = {}
        for r in itin_rows:
            i_id = r["itinerary_id"]
            if i_id not in itineraries_map:
                itineraries_map[i_id] = {
                    "id": i_id,
                    "day_number": r["day_number"],
                    "title": r["itinerary_title"],
                    "activities": [],
                }
            if r["activity_id"]:
                itineraries_map[i_id]["activities"].append({
                    "id": r["activity_id"],
                    "time_slot": r["time_slot"],
                    "place_name": r["place_name"],
                    "description": r["activity_desc"],
                })

        tour_dict["itineraries"] = list(itineraries_map.values())
        return tour_dict

    async def create_tour(
        self,
        title: str,
        description: str,
        category: str,
        destination: str,
        base_price_adult: Decimal,
        base_price_child: Decimal,
        max_participants: int,
        start_date: date,
        end_date: date,
        created_by: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tạo tour mới ở trạng thái DRAFT.
        Gọi function: fn_tao_tour(...)
        """
        sql = """
            SELECT * FROM fn_tao_tour(
                p_title := $1,
                p_description := $2,
                p_category := $3,
                p_destination := $4,
                p_base_price_adult := $5,
                p_base_price_child := $6,
                p_max_participants := $7,
                p_start_date := $8,
                p_end_date := $9,
                p_created_by := $10,
                p_ip_address := $11
            );
        """
        row = await self._conn.fetchrow(
            sql,
            title,
            description,
            category,
            destination,
            base_price_adult,
            base_price_child,
            max_participants,
            start_date,
            end_date,
            created_by,
            ip_address,
        )
        return dict(row) if row else {}

    async def add_itinerary(
        self,
        tour_id: uuid.UUID,
        day_number: int,
        title: str,
    ) -> Dict[str, Any]:
        """
        Thêm ngày lịch trình cho tour.
        Gọi function: fn_them_lich_trinh(...)
        """
        sql = "SELECT * FROM fn_them_lich_trinh($1, $2, $3);"
        row = await self._conn.fetchrow(sql, tour_id, day_number, title)
        return dict(row) if row else {}

    async def add_activity(
        self,
        itinerary_id: uuid.UUID,
        time_slot: Optional[time],
        place_name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Thêm hoạt động cụ thể vào một ngày trong lịch trình.
        Gọi function: fn_them_hoat_dong(...)
        """
        sql = "SELECT * FROM fn_them_hoat_dong($1, $2, $3, $4);"
        row = await self._conn.fetchrow(sql, itinerary_id, time_slot, place_name, description)
        return dict(row) if row else {}

    async def update_tour(
        self,
        tour_id: uuid.UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        destination: Optional[str] = None,
        base_price_adult: Optional[Decimal] = None,
        base_price_child: Optional[Decimal] = None,
        max_participants: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cập nhật thông tin tour (DRAFT hoặc PUBLISHED).
        Gọi function: fn_cap_nhat_tour(...)
        """
        sql = """
            SELECT * FROM fn_cap_nhat_tour(
                p_tour_id := $1,
                p_title := $2,
                p_description := $3,
                p_category := $4,
                p_destination := $5,
                p_base_price_adult := $6,
                p_base_price_child := $7,
                p_max_participants := $8,
                p_start_date := $9,
                p_end_date := $10,
                p_user_id := $11,
                p_ip_address := $12
            );
        """
        row = await self._conn.fetchrow(
            sql,
            tour_id,
            title,
            description,
            category,
            destination,
            base_price_adult,
            base_price_child,
            max_participants,
            start_date,
            end_date,
            user_id,
            ip_address,
        )
        return dict(row) if row else None

    async def publish_tour(
        self,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Xuất bản tour (DRAFT -> PUBLISHED).
        Gọi function: fn_xuat_ban_tour(...)
        """
        sql = "SELECT * FROM fn_xuat_ban_tour($1, $2, $3);"
        row = await self._conn.fetchrow(sql, tour_id, user_id, ip_address)
        return dict(row) if row else {}

    async def close_tour(
        self,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Đóng tour khi đã hoàn thành hoặc hết hạn (PUBLISHED -> ARCHIVED).
        Gọi function: fn_dong_tour(...)
        """
        sql = "SELECT * FROM fn_dong_tour($1, $2, $3);"
        row = await self._conn.fetchrow(sql, tour_id, user_id, ip_address)
        return dict(row) if row else {}

    async def cancel_tour(
        self,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Hủy tour (-> CANCELLED) và tự động hủy các booking chưa thanh toán.
        Gọi function: fn_huy_tour(...)
        """
        sql = "SELECT * FROM fn_huy_tour($1, $2, $3);"
        row = await self._conn.fetchrow(sql, tour_id, user_id, ip_address)
        return dict(row) if row else {}
