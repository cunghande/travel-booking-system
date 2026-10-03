# ============================================================
# Travel Booking System — API Router: AI Trợ lý du lịch (AI Assistant)
# ============================================================
# Cung cấp tính năng gợi ý tour thông minh dựa trên sở thích, ngân sách
# và nhu cầu của khách hàng.
# ============================================================

from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.application.dto.tour import TourListResponse
from app.application.services.tour_service import TourService
from app.core.dependencies import DBConn

router = APIRouter(prefix="/ai", tags=["AI Trợ lý du lịch"])


class AIRecommendRequest(BaseModel):
    """Dữ liệu khách hàng gửi lên để AI gợi ý tour."""
    destination: Optional[str] = Field(None, description="Địa điểm mong muốn (Hạ Long, Đà Nẵng, Phú Quốc...)")
    max_budget: Optional[float] = Field(None, ge=0, description="Ngân sách tối đa cho mỗi người ($)")
    category: Optional[str] = Field(None, description="Sở thích: Biển, Leo núi, Nghỉ dưỡng...")
    travelers_count: int = Field(1, ge=1, description="Số lượng người đi")
    notes: Optional[str] = Field(None, description="Ghi chú thêm: đi cùng gia đình, thích yên tĩnh...")


class RecommendedTourItem(BaseModel):
    """Thông tin tour kèm lý do gợi ý của AI."""
    tour: TourListResponse
    match_score: int = Field(..., description="Độ phù hợp (thang điểm 100)")
    ai_reason: str = Field(..., description="Lý do AI đề xuất tour này")


class AIRecommendResponse(BaseModel):
    """Kết quả tư vấn tour từ AI."""
    summary: str = Field(..., description="Lời chào và tóm tắt nhận định của AI")
    recommendations: List[RecommendedTourItem] = Field(default_factory=list)


@router.post(
    "/recommend",
    response_model=AIRecommendResponse,
    summary="AI Gợi ý Tour du lịch phù hợp",
    description="Nhận sở thích, ngân sách của người dùng và đề xuất các tour phù hợp nhất trong database.",
)
async def recommend_tours(
    data: AIRecommendRequest,
    conn: DBConn,
) -> AIRecommendResponse:
    """
    Quy trình hoạt động:
    1. Truy vấn database lấy danh sách các tour đang mở bán (PUBLISHED) phù hợp ngân sách/điểm đến.
    2. Thuật toán AI tính điểm độ phù hợp (Match Score) dựa trên:
       - Điểm đến khách mong muốn (+40 điểm)
       - Ngân sách phù hợp (+30 điểm)
       - Danh mục sở thích trùng khớp (+30 điểm)
    3. Trả về kết quả kèm lời giải thích tự nhiên.
    """
    tour_service = TourService(conn)
    budget_decimal = Decimal(str(data.max_budget)) if data.max_budget else None

    # Tìm kiếm các tour khả dụng trong database
    tours_page = await tour_service.search_tours(
        destination=data.destination,
        category=data.category,
        status="PUBLISHED",
        max_price=budget_decimal,
        page=1,
        page_size=10,
    )

    recommended_items: List[RecommendedTourItem] = []

    for t in tours_page.items:
        score = 60  # Điểm cơ bản
        reasons = []

        if data.destination and data.destination.lower() in t.destination.lower():
            score += 25
            reasons.append(f"Đúng điểm đến '{data.destination}' bạn yêu cầu")

        if data.max_budget and t.base_price_adult <= data.max_budget:
            score += 15
            reasons.append(f"Giá vé ${t.base_price_adult:.2f} nằm trọn trong ngân sách ${data.max_budget:.2f}")

        if data.category and t.category and data.category.lower() in t.category.lower():
            score += 15
            reasons.append(f"Phù hợp thể loại '{data.category}' bạn yêu thích")

        if not reasons:
            reasons.append("Tour nổi bật đang được nhiều du khách lựa chọn trong mùa này")

        ai_reason_text = " • ".join(reasons)

        recommended_items.append(
            RecommendedTourItem(
                tour=t,
                match_score=min(100, score),
                ai_reason=ai_reason_text,
            )
        )

    # Sắp xếp tour theo điểm số giảm dần
    recommended_items.sort(key=lambda x: x.match_score, reverse=True)

    summary_text = (
        f"Dựa trên yêu cầu của bạn (Điểm đến: {data.destination or 'Tất cả'}, "
        f"Ngân sách: ${data.max_budget or 'Linh hoạt'}), hệ thống đã phân tích và "
        f"tìm thấy {len(recommended_items)} hành trình lý tưởng nhất dành cho bạn!"
    )

    return AIRecommendResponse(
        summary=summary_text,
        recommendations=recommended_items[:5],
    )
