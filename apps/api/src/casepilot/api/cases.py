"""Demonstration case HTTP resources."""

from fastapi import APIRouter, HTTPException

from ..cases.repository import get_case, list_cases
from ..schemas.analysis import V0ClaimCase

router = APIRouter()


@router.get("/api/cases", response_model=list[V0ClaimCase], response_model_exclude_none=True)
async def cases():
    return list_cases()


@router.get("/api/cases/{case_id}", response_model=V0ClaimCase, response_model_exclude_none=True)
async def case(case_id: str):
    result = get_case(case_id)
    if result is None:
        raise HTTPException(404, f"Case {case_id} not found")
    return result
