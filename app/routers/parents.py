"""
routers/parents.py — Parent CRUD endpoints
Converted from: src/app/(dashboard)/list/parents/page.tsx
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Parent
from app.schemas import ParentCreate, ParentUpdate, ParentResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/parents", tags=["Parents"])


@router.get("", response_model=PaginatedResponse)
async def get_parents(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Parent).options(selectinload(Parent.students))

    if search:
        query = query.where(
            or_(
                Parent.name.ilike(f"%{search}%"),
                Parent.surname.ilike(f"%{search}%"),
                Parent.email.ilike(f"%{search}%"),
                Parent.phone.ilike(f"%{search}%"),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    parents = result.scalars().unique().all()

    return {
        "data": [ParentResponse.model_validate(p) for p in parents],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/{parent_id}", response_model=ParentResponse)
async def get_parent(
    parent_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    result = await db.execute(
        select(Parent).where(Parent.id == parent_id).options(selectinload(Parent.students))
    )
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    return parent


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_parent(
    data: ParentCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    parent = Parent(**data.model_dump())
    db.add(parent)
    await db.flush()
    await db.refresh(parent)
    return parent


@router.patch("/{parent_id}", response_model=ParentResponse)
async def update_parent(
    parent_id: int,
    data: ParentUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(parent, key, value)
    await db.flush()
    await db.refresh(parent)
    return parent


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parent(
    parent_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    await db.delete(parent)
