"""
routers/results.py — Results CRUD endpoints
Converted from: src/app/(dashboard)/list/results/page.tsx
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Result
from app.schemas import ResultCreate, ResultResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/results", tags=["Results"])


@router.get("", response_model=PaginatedResponse)
async def get_results(
    page: int = Query(1, ge=1),
    student_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Result)
    if student_id:
        query = query.where(Result.student_id == student_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    results = result.scalars().all()

    return {
        "data": [ResultResponse.model_validate(r) for r in results],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=ResultResponse, status_code=status.HTTP_201_CREATED)
async def create_result(
    data: ResultCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    result_obj = Result(**data.model_dump())
    db.add(result_obj)
    await db.flush()
    await db.refresh(result_obj)
    return result_obj
