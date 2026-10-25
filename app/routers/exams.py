"""
routers/exams.py — Exam CRUD endpoints
Converted from: src/app/(dashboard)/list/exams/page.tsx
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Exam
from app.schemas import ExamCreate, ExamUpdate, ExamResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/exams", tags=["Exams"])


@router.get("", response_model=PaginatedResponse)
async def get_exams(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Exam).options(
        selectinload(Exam.lesson).selectinload(Exam.lesson.property.mapper.class_.subject),
    )
    if search:
        query = query.where(Exam.title.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    exams = result.scalars().unique().all()

    return {
        "data": [ExamResponse.model_validate(e) for e in exams],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    data: ExamCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    exam = Exam(**data.model_dump())
    db.add(exam)
    await db.flush()
    await db.refresh(exam)
    return exam


@router.patch("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: int,
    data: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(exam, key, value)
    await db.flush()
    await db.refresh(exam)
    return exam


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    await db.delete(exam)
