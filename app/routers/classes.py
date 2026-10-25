"""
routers/classes.py — Class CRUD endpoints
Converted from: src/app/(dashboard)/list/classes/page.tsx
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Class
from app.schemas import ClassCreate, ClassUpdate, ClassResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/classes", tags=["Classes"])


@router.get("", response_model=PaginatedResponse)
async def get_classes(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Class).options(
        selectinload(Class.grade),
        selectinload(Class.supervisor),
    )
    if search:
        query = query.where(Class.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    classes = result.scalars().unique().all()

    return {
        "data": [ClassResponse.model_validate(c) for c in classes],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher")),
):
    result = await db.execute(
        select(Class)
        .where(Class.id == class_id)
        .options(selectinload(Class.grade), selectinload(Class.supervisor))
    )
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    data: ClassCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    class_ = Class(**data.model_dump())
    db.add(class_)
    await db.flush()
    await db.refresh(class_)
    return class_


@router.patch("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    data: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(class_, key, value)
    await db.flush()
    await db.refresh(class_)
    return class_


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Class).where(Class.id == class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="Class not found")
    await db.delete(class_)
