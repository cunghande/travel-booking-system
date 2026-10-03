# ============================================================
# Travel Booking System — Repository: Nhật ký hệ thống (Audit Repository)
# ============================================================
# Tầng truy xuất dữ liệu ghi nhận hoạt động và bảo mật (Audit Logs).
# Sử dụng hàm fn_ghi_nhat_ky trong PostgreSQL qua asyncpg thuần.
# ============================================================

import json
from typing import Any, Dict, Optional
import uuid
import asyncpg


class AuditRepository:
    """
    Repository chuyên ghi nhận nhật ký hệ thống (Audit Logs) để truy vết và bảo mật.
    """

    def __init__(self, conn: asyncpg.Connection):
        """
        Khởi tạo repository với kết nối asyncpg.
        """
        self._conn = conn

    async def create(
        self,
        *,
        user_id: Optional[uuid.UUID] = None,
        action: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[uuid.UUID]:
        """
        Ghi một bản ghi nhật ký mới.
        Gọi function: fn_ghi_nhat_ky(...)
        """
        details_json = json.dumps(details, ensure_ascii=False) if details else None

        sql = """
            SELECT fn_ghi_nhat_ky(
                p_user_id := $1,
                p_action := $2,
                p_resource := $3,
                p_resource_id := $4,
                p_details := $5::jsonb,
                p_ip_address := $6
            );
        """
        log_id = await self._conn.fetchval(
            sql,
            user_id,
            action,
            resource,
            resource_id,
            details_json,
            ip_address,
        )
        return log_id
