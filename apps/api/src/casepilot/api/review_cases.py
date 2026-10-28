"""Query and read prepared closed-claim review cases."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from ..cases.review_repository import (
    ReviewCaseDataError,
    get_review_case,
    list_review_cases,
    review_document,
)
from ..schemas.review_cases import ReviewCaseDetail, ReviewCaseListResponse, ReviewPreflight

router = APIRouter()


@router.get("/api/review-cases", response_model=ReviewCaseListResponse)
async def cases(
    request: Request,
    query_type: Literal["claim_number", "report_number", "plate_number"] | None = Query(
        default=None, alias="queryType"
    ),
    query: str | None = Query(default=None, max_length=100),
    closed_from: date | None = Query(default=None, alias="closedFrom"),
    closed_to: date | None = Query(default=None, alias="closedTo"),
    injury_status: Literal[
        "injury_reported", "no_injury_reported", "unknown", "conflicting_information"
    ]
    | None = Query(default=None, alias="injuryStatus"),
    review_status: Literal[
        "not_started",
        "running",
        "pending_review",
        "pending_verification",
        "vehicle_review_completed",
        "failed",
        "awaiting_recovery",
    ]
    | None = Query(default=None, alias="reviewStatus"),
):
    normalized = query.strip() if query else None
    if normalized and query_type is None:
        raise HTTPException(400, "提供查询关键字时必须选择查询类型。")
    if closed_from and closed_to and closed_from > closed_to:
        raise HTTPException(400, "结案开始日期不能晚于结束日期。")
    try:
        return list_review_cases(
            query_type=query_type,
            query=normalized,
            closed_from=closed_from,
            closed_to=closed_to,
            injury_status=injury_status,
            review_status=review_status,
            latest_statuses=request.app.state.analyses.latest_review_statuses(),
        )
    except ReviewCaseDataError as error:
        raise HTTPException(500, str(error)) from error


@router.get("/api/review-cases/{case_id}", response_model=ReviewCaseDetail)
async def case(case_id: str, request: Request):
    try:
        result = get_review_case(case_id)
    except ReviewCaseDataError as error:
        raise HTTPException(500, str(error)) from error
    if result is None:
        raise HTTPException(404, f"Case {case_id} not found")
    result["latestReviewStatus"] = request.app.state.analyses.latest_review_statuses().get(
        case_id, "not_started"
    )
    return result


@router.get("/api/review-cases/{case_id}/review-preflight", response_model=ReviewPreflight)
async def review_preflight(case_id: str, request: Request):
    return await request.app.state.analyses.preflight(case_id)


@router.get("/api/review-cases/{case_id}/documents/{document_id}/content")
async def document(case_id: str, document_id: str):
    try:
        result = review_document(case_id, document_id)
    except ReviewCaseDataError as error:
        raise HTTPException(409, str(error)) from error
    if result is None:
        raise HTTPException(404, "案件材料不存在或当前不可读取。")
    path, title = result
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{title}.pdf" if not title.lower().endswith(".pdf") else title,
        content_disposition_type="inline",
    )
