"""
routers/events.py — Event CRUD endpoints
Converted from: src/app/(dashboard)/list/events (part of data.ts eventsData)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Event
from app.schemas import EventCreate, EventUpdate, EventResponse, PaginatedResponse
from app.auth import require_roles
from app.config import settings

router = APIRouter(prefix="/list/events", tags=["Events"])


@router.get("", response_model=PaginatedResponse)
async def get_events(
    page: int = Query(1, ge=1),
    class_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    per_page = settings.items_per_page
    offset = (page - 1) * per_page

    query = select(Event)
    if class_id:
        query = query.where(Event.class_id == class_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(query.offset(offset).limit(per_page))
    events = result.scalars().all()

    return {
        "data": [EventResponse.model_validate(e) for e in events],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    event = Event(**data.model_dump())
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(event, key, value)
    await db.flush()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
