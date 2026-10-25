"""
routers/teachers.py — Teacher CRUD endpoints
Converted from: src/app/(dashboard)/list/teachers/page.tsx + Prisma queries
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Teacher, Subject
from app.schemas import TeacherCreate, TeacherUpdate, TeacherResponse, PaginatedResponse
from app.auth import require_roles, get_user_role
from app.config import settings

router = APIRouter(prefix="/list/teachers", tags=["Teachers"])


@router.get("", response_model=PaginatedResponse)
async def get_teachers(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    """
    List all teachers with pagination and optional search.
    Equivalent to: TeacherList component + prisma.teacher.findMany()
    """
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Teacher).options(
        selectinload(Teacher.subjects),
        selectinload(Teacher.classes),
    )

    if search:
        query = query.where(
            or_(
                Teacher.name.ilike(f"%{search}%"),
                Teacher.surname.ilike(f"%{search}%"),
                Teacher.email.ilike(f"%{search}%"),
                Teacher.username.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Fetch page
    result = await db.execute(query.offset(offset).limit(per_page))
    teachers = result.scalars().unique().all()

    return {
        "data": [TeacherResponse.model_validate(t) for t in teachers],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    """Get a single teacher by ID."""
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.subjects), selectinload(Teacher.classes))
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """Create a new teacher (admin only)."""
    subject_ids = data.subject_ids
    teacher_data = data.model_dump(exclude={"subject_ids"})
    teacher = Teacher(**teacher_data)

    if subject_ids:
        subjects_result = await db.execute(
            select(Subject).where(Subject.id.in_(subject_ids))
        )
        teacher.subjects = subjects_result.scalars().all()

    db.add(teacher)
    await db.flush()
    await db.refresh(teacher)
    return teacher


@router.patch("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """Update a teacher (admin only)."""
    result = await db.execute(
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.subjects), selectinload(Teacher.classes))
    )
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"subject_ids"})
    for key, value in update_data.items():
        setattr(teacher, key, value)

    if data.subject_ids is not None:
        subjects_result = await db.execute(
            select(Subject).where(Subject.id.in_(data.subject_ids))
        )
        teacher.subjects = subjects_result.scalars().all()

    await db.flush()
    await db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """Delete a teacher (admin only)."""
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    await db.delete(teacher)
