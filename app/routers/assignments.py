"""
routers/assignments.py — Assignment CRUD endpoints
Converted from: src/app/(dashboard)/list/assignments/page.tsx
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Assignment
from app.schemas import AssignmentCreate, AssignmentUpdate, AssignmentResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/assignments", tags=["Assignments"])


@router.get("", response_model=PaginatedResponse)
async def get_assignments(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Assignment).options(selectinload(Assignment.lesson))
    if search:
        query = query.where(Assignment.title.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    assignments = result.scalars().unique().all()

    return {
        "data": [AssignmentResponse.model_validate(a) for a in assignments],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    assignment = Assignment(**data.model_dump())
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, key, value)
    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await db.delete(assignment)
