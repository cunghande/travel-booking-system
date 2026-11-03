import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
import aiomysql

from common.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from common.security import get_current_user
from services.tour_service.database import get_db
from services.tour_service.schemas import (
    TourCreateRequest, TourUpdateRequest,
    TourResponse, TourListResponse,
    ItineraryResponse, ActivityResponse,
)

router = APIRouter(prefix="/tours", tags=["Quản lý Tour"])

# HELPER: Ghép itineraries + activities vào tour dict
def _build_tour_response(tour: Dict, itineraries: list, activities: list) -> Dict:
    # Tạo map itinerary_id -> list activities
    act_map: Dict[str, list] = {}
    for act in activities:
        act_map.setdefault(act["itinerary_id"], []).append(act)

    # Ghép activities vào từng itinerary
    for itin in itineraries:
        itin["activities"] = act_map.get(itin["id"], [])

    tour["itineraries"] = itineraries
    return tour


# GET/tour : Lấy danh sách tour
@router.get("", response_model=TourListResponse, summary="Danh sách tour")
async def list_tours(
    destination: Optional[str] = Query(None, description="Lọc theo điểm đến"),
    category: Optional[str] = Query(None, description="Lọc theo danh mục"),
    status_filter: Optional[str] = Query(None, alias="status", description="Lọc theo trạng thái"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    conn: aiomysql.Connection = Depends(get_db),
):
    offset = (page - 1) * size
    async with conn.cursor() as cur:
        # Gọi procedure lấy danh sách (OUT param p_total)
        await cur.callproc("sp_get_tours", (destination, category, status_filter, size, offset, 0))
        # Lấy result set danh sách tour
        tours_raw = await cur.fetchall()
        # Lấy giá trị OUT param total
        await cur.execute("SELECT @_sp_get_tours_5 AS total")
        total = (await cur.fetchone())["total"] or 0

    # Lấy itineraries + activities cho từng tour (gọi sp_get_tour_by_id)
    items = []
    async with conn.cursor() as cur:
        for t in tours_raw:
            await cur.callproc("sp_get_tour_by_id", (t["id"],))
            tour_info = await cur.fetchone()
            await cur.nextset()
            itineraries = list(await cur.fetchall())
            await cur.nextset()
            activities = list(await cur.fetchall())
            if tour_info:
                items.append(TourResponse(**_build_tour_response(tour_info, itineraries, activities)))

    return TourListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=-(-total // size),
    )

#GET/tour/{tour_id}: Chi tiết 1 tour
@router.get("/{tour_id}", response_model=TourResponse, summary="Chi tiết 1 tour")
async def get_tour(
    tour_id: str,
    conn: aiomysql.Connection = Depends(get_db),
):
    async with conn.cursor() as cur:
        await cur.callproc("sp_get_tour_by_id", (tour_id,))
        tour = await cur.fetchone()
        await cur.nextset()
        itineraries = list(await cur.fetchall())
        await cur.nextset()
        activities = list(await cur.fetchall())

    if not tour:
        raise NotFoundError("Tour", tour_id)

    return TourResponse(**_build_tour_response(tour, itineraries, activities))


# Tạo tour
@router.post("", response_model=TourResponse, status_code=status.HTTP_201_CREATED,
             summary="Tạo tour mới (yêu cầu ADMIN hoặc STAFF)")
async def create_tour(
    data: TourCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_db),
):
    if current_user.get("role") not in ("ADMIN", "STAFF"):
        raise ForbiddenError("Chi ADMIN hoac STAFF moi duoc tao tour")

    if data.end_date <= data.start_date:
        raise BadRequestError("Ngay ket thuc phai sau ngay bat dau")

    tour_id = str(uuid.uuid4())
    created_by = current_user.get("user_id")

    async with conn.cursor() as cur:
        try:
            await cur.callproc("sp_create_tour", (
                tour_id, data.tour_code, data.title, data.description,
                data.category, data.destination,
                data.base_price_adult, data.base_price_child,
                data.max_participants, data.start_date, data.end_date, created_by,
            ))
            await cur.fetchall()  # Lấy hết result set của sp_create_tour
        except Exception as e:
            err = str(e)
            if "Ma tour da ton tai" in err or "45000" in err:
                raise ConflictError(f"Ma tour '{data.tour_code}' da ton tai")
            raise BadRequestError(f"Tao tour that bai: {err}")

        # Tạo itineraries và activities
        for itin in data.itineraries:
            itin_id = str(uuid.uuid4())
            await cur.callproc("sp_add_itinerary", (
                itin_id, tour_id, itin.day_number, itin.title,
            ))
            await cur.fetchall()
            for act in itin.activities:
                await cur.callproc("sp_add_activity", (
                    str(uuid.uuid4()), itin_id,
                    act.time_slot, act.place_name,
                    act.description, act.latitude, act.longitude,
                ))
                await cur.fetchall()

        # Lấy tour vừa tạo để trả về
        await cur.callproc("sp_get_tour_by_id", (tour_id,))
        tour = await cur.fetchone()
        await cur.nextset()
        itineraries = list(await cur.fetchall())
        await cur.nextset()
        activities = list(await cur.fetchall())

    return TourResponse(**_build_tour_response(tour, itineraries, activities))

# cập nhập tour
@router.put("/{tour_id}", response_model=TourResponse, summary="Cap nhat tour")
async def update_tour(
    tour_id: str,
    data: TourUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_db),
):
    if current_user.get("role") not in ("ADMIN", "STAFF"):
        raise ForbiddenError("Chi ADMIN hoac STAFF moi duoc cap nhat tour")

    d = data.model_dump()
    async with conn.cursor() as cur:
        try:
            await cur.callproc("sp_update_tour", (
                tour_id,
                d.get("title"), d.get("description"), d.get("category"),
                d.get("destination"), d.get("base_price_adult"), d.get("base_price_child"),
                d.get("max_participants"), d.get("start_date"), d.get("end_date"),
                d.get("status"),
            ))
            await cur.fetchall()
        except Exception as e:
            if "Tour khong ton tai" in str(e) or "45000" in str(e):
                raise NotFoundError("Tour", tour_id)
            raise BadRequestError(str(e))

        await cur.callproc("sp_get_tour_by_id", (tour_id,))
        tour = await cur.fetchone()
        await cur.nextset()
        itineraries = list(await cur.fetchall())
        await cur.nextset()
        activities = list(await cur.fetchall())

    return TourResponse(**_build_tour_response(tour, itineraries, activities))

# Hủy tour
@router.delete("/{tour_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Huy tour - chi ADMIN")
async def cancel_tour(
    tour_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: aiomysql.Connection = Depends(get_db),
):
    if current_user.get("role") != "ADMIN":
        raise ForbiddenError("Chi ADMIN moi duoc huy tour")

    async with conn.cursor() as cur:
        try:
            await cur.callproc("sp_cancel_tour", (tour_id,))
            await cur.fetchall()
        except Exception as e:
            if "Tour khong ton tai" in str(e) or "45000" in str(e):
                raise NotFoundError("Tour", tour_id)
            raise BadRequestError(str(e))
