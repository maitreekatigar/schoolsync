"""
routers/dashboard.py — Dashboard statistics endpoints
Converted from:
  - src/components/dashboard/UserCard.tsx
  - src/components/dashboard/AttendanceChart.tsx
  - src/components/dashboard/FinanceChart.tsx
  - src/components/dashboard/PieChart.tsx (sex ratio)
  - src/components/dashboard/Announcements.tsx
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import (
    Student, Teacher, Parent, Admin,
    Attendance, Announcement, Event, UserSex
)
from app.auth import require_roles

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """
    Returns counts for the 4 UserCards on the admin dashboard.
    Equivalent to: UserCard component showing 620 (hardcoded) → now real data.
    """
    student_count = (await db.execute(select(func.count()).select_from(Student))).scalar_one()
    teacher_count = (await db.execute(select(func.count()).select_from(Teacher))).scalar_one()
    parent_count = (await db.execute(select(func.count()).select_from(Parent))).scalar_one()
    admin_count = (await db.execute(select(func.count()).select_from(Admin))).scalar_one()

    return {
        "students": student_count,
        "teachers": teacher_count,
        "parents": parent_count,
        "staff": admin_count,
        "academic_year": "2024-25",
    }


@router.get("/sex-ratio")
async def get_sex_ratio(
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """
    Returns male/female ratio for students.
    Equivalent to: PieChart component (sex ratio chart).
    """
    result = await db.execute(
        select(Student.sex, func.count(Student.id)).group_by(Student.sex)
    )
    rows = result.all()
    data = {row[0].value: row[1] for row in rows}

    return {
        "male": data.get("MALE", 0),
        "female": data.get("FEMALE", 0),
    }


@router.get("/attendance-chart")
async def get_attendance_chart(
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """
    Returns weekly attendance data for AttendanceChart.
    Equivalent to: src/components/dashboard/AttendanceChart.tsx
    """
    from sqlalchemy import extract, cast, Date

    result = await db.execute(
        select(
            func.date_trunc("week", Attendance.date).label("week"),
            func.count(Attendance.id).filter(Attendance.present == True).label("present"),
            func.count(Attendance.id).filter(Attendance.present == False).label("absent"),
        ).group_by("week").order_by("week").limit(10)
    )
    rows = result.all()

    return [
        {
            "week": str(row.week),
            "present": row.present,
            "absent": row.absent,
        }
        for row in rows
    ]


@router.get("/announcements")
async def get_recent_announcements(
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin")),
):
    """
    Returns the 5 most recent announcements.
    Equivalent to: Announcements component (hardcoded data → real DB).
    """
    result = await db.execute(
        select(Announcement).order_by(Announcement.date.desc()).limit(5)
    )
    announcements = result.scalars().all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "description": a.description,
            "date": a.date.isoformat(),
            "class_id": a.class_id,
        }
        for a in announcements
    ]


@router.get("/events")
async def get_upcoming_events(
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_roles("admin", "teacher", "student", "parent")),
):
    """
    Returns upcoming events for the EventCalendar component.
    Equivalent to: src/components/dashboard/EventCalendar.tsx
    """
    from datetime import datetime
    result = await db.execute(
        select(Event)
        .where(Event.start_time >= datetime.now())
        .order_by(Event.start_time)
        .limit(10)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "class_id": e.class_id,
        }
        for e in events
    ]
