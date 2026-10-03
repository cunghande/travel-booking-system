# ============================================================
# Travel Booking System — Repository: Đặt tour (Booking Repository)
# ============================================================
# Tầng truy xuất dữ liệu Đơn đặt tour (Booking) qua asyncpg.
# Gọi trực tiếp các Stored Procedures trong PostgreSQL — Không ORM.
# ============================================================

from typing import Any, Dict, List, Optional, Tuple
import uuid
import asyncpg


class BookingRepository:
    """
    Repository phụ trách toàn bộ thao tác dữ liệu liên quan đến Booking và Hành khách (Passenger).
    Bao gồm kiểm tra số chỗ trống, tạo mã đơn, tự tính tiền và hoàn trả vé an toàn giao dịch.
    """

    def __init__(self, conn: asyncpg.Connection):
        """
        Khởi tạo repository với kết nối asyncpg.
        conn được inject tự động từ get_db dependency.
        """
        self._conn = conn

    async def create_booking(
        self,
        user_id: uuid.UUID,
        tour_id: uuid.UUID,
        num_adults: int,
        num_children: int = 0,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        special_requests: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tạo đơn đặt tour mới.
        Function PostgreSQL tự động kiểm tra available_slots với khóa dòng FOR UPDATE,
        tính tổng tiền vé và trừ số chỗ an toàn race condition.
        Gọi function: fn_tao_don_dat_tour(...)
        """
        sql = """
            SELECT * FROM fn_tao_don_dat_tour(
                p_user_id := $1,
                p_tour_id := $2,
                p_num_adults := $3,
                p_num_children := $4,
                p_contact_name := $5,
                p_contact_email := $6,
                p_contact_phone := $7,
                p_special_requests := $8,
                p_ip_address := $9
            );
        """
        row = await self._conn.fetchrow(
            sql,
            user_id,
            tour_id,
            num_adults,
            num_children,
            contact_name,
            contact_email,
            contact_phone,
            special_requests,
            ip_address,
        )
        return dict(row) if row else {}

    async def add_passenger(
        self,
        booking_id: uuid.UUID,
        full_name: str,
        passenger_type: str = "ADULT",
        id_card_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Thêm hành khách vào danh sách chi tiết của đơn đặt tour.
        Gọi function: fn_them_hanh_khach(...)
        """
        sql = """
            SELECT * FROM fn_them_hanh_khach(
                p_booking_id := $1,
                p_full_name := $2,
                p_passenger_type := $3,
                p_id_card_number := $4
            );
        """
        row = await self._conn.fetchrow(sql, booking_id, full_name, passenger_type, id_card_number)
        return dict(row) if row else {}

    async def get_by_id(self, booking_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin chi tiết một đơn đặt tour kèm danh sách hành khách đi kèm.
        Gọi:
          1. fn_lay_chi_tiet_booking(p_booking_id)
          2. fn_lay_hanh_khach_booking(p_booking_id)
        """
        booking_sql = "SELECT * FROM fn_lay_chi_tiet_booking($1);"
        booking_row = await self._conn.fetchrow(booking_sql, booking_id)
        if not booking_row:
            return None

        booking_dict = dict(booking_row)

        # Lấy danh sách hành khách
        passengers_sql = "SELECT * FROM fn_lay_hanh_khach_booking($1);"
        passengers_rows = await self._conn.fetch(passengers_sql, booking_id)
        booking_dict["passengers"] = [dict(r) for r in passengers_rows]

        return booking_dict

    async def get_by_code(self, booking_code: str) -> Optional[Dict[str, Any]]:
        """
        Tìm đơn đặt tour theo mã code (Ví dụ: BK-XXXXXXXX).
        """
        sql = """
            SELECT b.id FROM bookings b WHERE b.booking_code = $1;
        """
        row = await self._conn.fetchrow(sql, booking_code.strip().upper())
        if not row:
            return None
        return await self.get_by_id(row["id"])

    async def get_my_bookings(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lấy lịch sử đơn đặt tour của cá nhân khách hàng.
        Gọi function: fn_lay_booking_cua_toi(...)
        """
        sql = "SELECT * FROM fn_lay_booking_cua_toi($1, $2, $3);"
        rows = await self._conn.fetch(sql, user_id, skip, limit)
        if not rows:
            return [], 0

        items = [dict(r) for r in rows]
        total = items[0]["total_count"] if items else 0
        return items, total

    async def get_all_bookings(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        tour_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lấy toàn bộ danh sách đơn đặt tour (Dành cho Admin / Staff).
        Gọi function: fn_lay_tat_ca_booking(...)
        """
        sql = "SELECT * FROM fn_lay_tat_ca_booking($1, $2, $3, $4);"
        rows = await self._conn.fetch(sql, skip, limit, status, tour_id)
        if not rows:
            return [], 0

        items = [dict(r) for r in rows]
        total = items[0]["total_count"] if items else 0
        return items, total

    async def cancel_booking(
        self,
        booking_id: uuid.UUID,
        current_user_id: uuid.UUID,
        is_admin: bool = False,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Hủy đơn đặt tour và tự động hoàn trả chỗ trống cho tour.
        Gọi function: fn_huy_don_dat_tour(...)
        """
        sql = "SELECT * FROM fn_huy_don_dat_tour($1, $2, $3, $4);"
        row = await self._conn.fetchrow(sql, booking_id, current_user_id, is_admin, ip_address)
        return dict(row) if row else {}

    async def confirm_booking(
        self,
        booking_id: uuid.UUID,
        admin_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Xác nhận đơn đặt tour đã duyệt thanh toán (Admin / Staff).
        Gọi function: fn_xac_nhan_don_dat_tour(...)
        """
        sql = "SELECT * FROM fn_xac_nhan_don_dat_tour($1, $2, $3);"
        row = await self._conn.fetchrow(sql, booking_id, admin_id, ip_address)
        return dict(row) if row else {}
