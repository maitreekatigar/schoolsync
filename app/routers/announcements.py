"""
routers/announcements.py — Announcement CRUD endpoints
Converted from: src/components/dashboard/Announcements.tsx + announcementsData
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Announcement
from app.schemas import AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/announcements", tags=["Announcements"])


@router.get("", response_model=PaginatedResponse)
async def get_announcements(
    page: int = Query(1, ge=1),
    class_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Announcement).order_by(Announcement.date.desc())
    if class_id:
        query = query.where(Announcement.class_id == class_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    announcements = result.scalars().all()

    return {
        "data": [AnnouncementResponse.model_validate(a) for a in announcements],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    ann = Announcement(**data.model_dump())
    db.add(ann)
    await db.flush()
    await db.refresh(ann)
    return ann


@router.patch("/{ann_id}", response_model=AnnouncementResponse)
async def update_announcement(
    ann_id: int,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ann, key, value)
    await db.flush()
    await db.refresh(ann)
    return ann


@router.delete("/{ann_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    ann_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Announcement).where(Announcement.id == ann_id))
    ann = result.scalar_one_or_none()
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await db.delete(ann)
