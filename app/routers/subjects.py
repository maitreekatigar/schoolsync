"""
routers/subjects.py — Subject endpoints
Converted from: src/app/(dashboard)/list/subjects (admin only)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Subject
from app.schemas import SubjectCreate, SubjectResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/subjects", tags=["Subjects"])


@router.get("", response_model=PaginatedResponse)
async def get_subjects(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Subject).options(selectinload(Subject.teachers))
    if search:
        query = query.where(Subject.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    subjects = result.scalars().unique().all()

    return {
        "data": [SubjectResponse.model_validate(s) for s in subjects],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    data: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    subject = Subject(**data.model_dump())
    db.add(subject)
    await db.flush()
    await db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    await db.delete(subject)
