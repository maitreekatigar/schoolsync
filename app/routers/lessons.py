"""
routers/lessons.py — Lesson CRUD endpoints
Converted from: src/app/(dashboard)/list/lessons/page.tsx
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Lesson
from app.schemas import LessonCreate, LessonUpdate, LessonResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/lessons", tags=["Lessons"])


@router.get("", response_model=PaginatedResponse)
async def get_lessons(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    class_id: Optional[int] = Query(None),
    teacher_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Lesson).options(
        selectinload(Lesson.subject),
        selectinload(Lesson.class_),
        selectinload(Lesson.teacher),
    )
    if search:
        query = query.where(Lesson.name.ilike(f"%{search}%"))
    if class_id:
        query = query.where(Lesson.class_id == class_id)
    if teacher_id:
        query = query.where(Lesson.teacher_id == teacher_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    lessons = result.scalars().unique().all()

    return {
        "data": [LessonResponse.model_validate(l) for l in lessons],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    lesson = Lesson(**data.model_dump())
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    await db.delete(lesson)
