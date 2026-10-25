"""
routers/students.py — Student CRUD endpoints
Converted from: src/app/(dashboard)/list/students/page.tsx + Prisma queries
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Student
from app.schemas import StudentCreate, StudentUpdate, StudentResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/students", tags=["Students"])


@router.get("", response_model=PaginatedResponse)
async def get_students(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    class_id: Optional[int] = Query(None),
    grade_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    """List all students with pagination, search, class/grade filters."""
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Student).options(
        selectinload(Student.parent),
        selectinload(Student.class_),
        selectinload(Student.grade),
    )

    if search:
        query = query.where(
            or_(
                Student.name.ilike(f"%{search}%"),
                Student.surname.ilike(f"%{search}%"),
                Student.username.ilike(f"%{search}%"),
            )
        )
    if class_id:
        query = query.where(Student.class_id == class_id)
    if grade_id:
        query = query.where(Student.grade_id == grade_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    students = result.scalars().unique().all()

    return {
        "data": [StudentResponse.model_validate(s) for s in students],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    result = await db.execute(
        select(Student)
        .where(Student.id == student_id)
        .options(
            selectinload(Student.parent),
            selectinload(Student.class_),
            selectinload(Student.grade),
        )
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    student = Student(**data.model_dump())
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)

    await db.flush()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    await db.delete(student)
