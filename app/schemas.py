"""
schemas.py — Pydantic v2 request/response models
Converted from: Zod schemas + TypeScript types
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from app.models import UserSex, Day


# ── Shared / Base ────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    per_page: int
    total_pages: int


# ── Admin ────────────────────────────────────────────────────────────────────

class AdminBase(BaseModel):
    username: str
    name: str
    surname: str
    email: EmailStr
    phone: Optional[str] = None


class AdminCreate(AdminBase):
    pass


class AdminResponse(AdminBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Grade ────────────────────────────────────────────────────────────────────

class GradeResponse(BaseModel):
    id: int
    level: int

    class Config:
        from_attributes = True


# ── Subject ──────────────────────────────────────────────────────────────────

class SubjectBase(BaseModel):
    name: str


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase):
    id: int

    class Config:
        from_attributes = True


# ── Parent ───────────────────────────────────────────────────────────────────

class ParentBase(BaseModel):
    username: str
    name: str
    surname: str
    email: Optional[EmailStr] = None
    phone: str
    address: str


class ParentCreate(ParentBase):
    pass


class ParentUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class ParentResponse(ParentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Teacher ───────────────────────────────────────────────────────────────────

class TeacherBase(BaseModel):
    username: str
    name: str
    surname: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: str
    img: Optional[str] = None
    blood_type: str
    sex: UserSex
    birthday: datetime


class TeacherCreate(TeacherBase):
    subject_ids: List[int] = []


class TeacherUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    img: Optional[str] = None
    blood_type: Optional[str] = None
    sex: Optional[UserSex] = None
    birthday: Optional[datetime] = None
    subject_ids: Optional[List[int]] = None


class TeacherResponse(TeacherBase):
    id: int
    created_at: datetime
    subjects: List[SubjectResponse] = []
    classes: List["ClassSummary"] = []

    class Config:
        from_attributes = True


# ── Class ────────────────────────────────────────────────────────────────────

class ClassSummary(BaseModel):
    id: int
    name: str
    capacity: int

    class Config:
        from_attributes = True


class ClassBase(BaseModel):
    name: str
    capacity: int
    grade_id: int
    supervisor_id: Optional[int] = None


class ClassCreate(ClassBase):
    pass


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    grade_id: Optional[int] = None
    supervisor_id: Optional[int] = None


class ClassResponse(ClassBase):
    id: int
    grade: GradeResponse
    supervisor: Optional["TeacherSummary"] = None

    class Config:
        from_attributes = True


class TeacherSummary(BaseModel):
    id: int
    name: str
    surname: str

    class Config:
        from_attributes = True


# ── Student ───────────────────────────────────────────────────────────────────

class StudentBase(BaseModel):
    username: str
    name: str
    surname: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: str
    img: Optional[str] = None
    blood_type: str
    sex: UserSex
    birthday: datetime
    parent_id: int
    class_id: int
    grade_id: int


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    img: Optional[str] = None
    blood_type: Optional[str] = None
    sex: Optional[UserSex] = None
    birthday: Optional[datetime] = None
    parent_id: Optional[int] = None
    class_id: Optional[int] = None
    grade_id: Optional[int] = None


class StudentResponse(StudentBase):
    id: int
    created_at: datetime
    parent: Optional[ParentResponse] = None
    class_: Optional[ClassSummary] = None
    grade: Optional[GradeResponse] = None

    class Config:
        from_attributes = True


# ── Lesson ────────────────────────────────────────────────────────────────────

class LessonBase(BaseModel):
    name: str
    day: Day
    start_time: datetime
    end_time: datetime
    subject_id: int
    class_id: int
    teacher_id: int


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    name: Optional[str] = None
    day: Optional[Day] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    subject_id: Optional[int] = None
    class_id: Optional[int] = None
    teacher_id: Optional[int] = None


class LessonResponse(LessonBase):
    id: int
    subject: SubjectResponse
    class_: ClassSummary
    teacher: TeacherSummary

    class Config:
        from_attributes = True


# ── Exam ──────────────────────────────────────────────────────────────────────

class ExamBase(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    lesson_id: int


class ExamCreate(ExamBase):
    pass


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    lesson_id: Optional[int] = None


class ExamResponse(ExamBase):
    id: int
    lesson: LessonResponse

    class Config:
        from_attributes = True


# ── Assignment ────────────────────────────────────────────────────────────────

class AssignmentBase(BaseModel):
    title: str
    start_date: datetime
    due_date: datetime
    lesson_id: int


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    lesson_id: Optional[int] = None


class AssignmentResponse(AssignmentBase):
    id: int
    lesson: LessonResponse

    class Config:
        from_attributes = True


# ── Result ────────────────────────────────────────────────────────────────────

class ResultBase(BaseModel):
    score: int
    exam_id: Optional[int] = None
    assignment_id: Optional[int] = None
    student_id: int


class ResultCreate(ResultBase):
    pass


class ResultResponse(ResultBase):
    id: int

    class Config:
        from_attributes = True


# ── Attendance ────────────────────────────────────────────────────────────────

class AttendanceBase(BaseModel):
    date: datetime
    present: bool
    student_id: int
    lesson_id: int


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceResponse(AttendanceBase):
    id: int

    class Config:
        from_attributes = True


# ── Event ─────────────────────────────────────────────────────────────────────

class EventBase(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    class_id: Optional[int] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    class_id: Optional[int] = None


class EventResponse(EventBase):
    id: int

    class Config:
        from_attributes = True


# ── Announcement ──────────────────────────────────────────────────────────────

class AnnouncementBase(BaseModel):
    title: str
    description: str
    date: datetime
    class_id: Optional[int] = None


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    class_id: Optional[int] = None


class AnnouncementResponse(AnnouncementBase):
    id: int

    class Config:
        from_attributes = True


# Resolve forward references
TeacherResponse.model_rebuild()
ClassResponse.model_rebuild()
