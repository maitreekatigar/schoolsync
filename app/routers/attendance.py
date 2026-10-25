"""
routers/attendance.py — Attendance endpoints
Converted from: src/app/(dashboard)/list/attendance
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date

from app.database import get_db
from app.models import Attendance
from app.schemas import AttendanceCreate, AttendanceResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/attendance", tags=["Attendance"])


@router.get("", response_model=PaginatedResponse)
async def get_attendance(
    page: int = Query(1, ge=1),
    student_id: Optional[int] = Query(None),
    lesson_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Attendance)
    if student_id:
        query = query.where(Attendance.student_id == student_id)
    if lesson_id:
        query = query.where(Attendance.lesson_id == lesson_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    records = result.scalars().all()

    return {
        "data": [AttendanceResponse.model_validate(r) for r in records],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=AttendanceResponse)
async def create_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    record = Attendance(**data.model_dump())
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record
