"""
models.py — SQLAlchemy ORM models
Converted from: prisma/schema.prisma
"""
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Integer, String, Boolean, DateTime, Enum as SAEnum,
    ForeignKey, Table, Column, func, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


# ── Enums (from Prisma schema) ──────────────────────────────────────────────

class UserSex(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class Day(str, enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"


# ── Association Tables (many-to-many) ───────────────────────────────────────

teacher_subjects = Table(
    "teacher_subjects",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subjects.id"), primary_key=True),
)

teacher_classes = Table(
    "teacher_classes",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
    Column("class_id", Integer, ForeignKey("classes.id"), primary_key=True),
)


# ── Models ───────────────────────────────────────────────────────────────────

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    level: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    students: Mapped[List["Student"]] = relationship("Student", back_populates="grade")
    classes: Mapped[List["Class"]] = relationship("Class", back_populates="grade")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher", secondary=teacher_subjects, back_populates="subjects"
    )
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="subject")


class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    students: Mapped[List["Student"]] = relationship("Student", back_populates="parent")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=False)
    img: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    blood_type: Mapped[str] = mapped_column(String, nullable=False)
    sex: Mapped[UserSex] = mapped_column(SAEnum(UserSex), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    birthday: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    subjects: Mapped[List["Subject"]] = relationship(
        "Subject", secondary=teacher_subjects, back_populates="teachers"
    )
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="teacher")
    classes: Mapped[List["Class"]] = relationship(
        "Class", secondary=teacher_classes, back_populates="teachers"
    )
    supervised_classes: Mapped[List["Class"]] = relationship(
        "Class", foreign_keys="[Class.supervisor_id]", back_populates="supervisor"
    )


class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    grade_id: Mapped[int] = mapped_column(Integer, ForeignKey("grades.id"), nullable=False)
    supervisor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("teachers.id"), nullable=True
    )

    grade: Mapped["Grade"] = relationship("Grade", back_populates="classes")
    supervisor: Mapped[Optional["Teacher"]] = relationship(
        "Teacher", foreign_keys=[supervisor_id], back_populates="supervised_classes"
    )
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher", secondary=teacher_classes, back_populates="classes"
    )
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="class_")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="class_")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="class_")
    announcements: Mapped[List["Announcement"]] = relationship(
        "Announcement", back_populates="class_"
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    address: Mapped[str] = mapped_column(String, nullable=False)
    img: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    blood_type: Mapped[str] = mapped_column(String, nullable=False)
    sex: Mapped[UserSex] = mapped_column(SAEnum(UserSex), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    birthday: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, ForeignKey("parents.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), nullable=False)
    grade_id: Mapped[int] = mapped_column(Integer, ForeignKey("grades.id"), nullable=False)

    parent: Mapped["Parent"] = relationship("Parent", back_populates="students")
    class_: Mapped["Class"] = relationship("Class", back_populates="students")
    grade: Mapped["Grade"] = relationship("Grade", back_populates="students")
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="student"
    )
    results: Mapped[List["Result"]] = relationship("Result", back_populates="student")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    day: Mapped[Day] = mapped_column(SAEnum(Day), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="lessons")
    class_: Mapped["Class"] = relationship("Class", back_populates="lessons")
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="lessons")
    exams: Mapped[List["Exam"]] = relationship("Exam", back_populates="lesson")
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="lesson"
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="lesson"
    )


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id"), nullable=False)

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="exams")
    results: Mapped[List["Result"]] = relationship("Result", back_populates="exam")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id"), nullable=False)

    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="assignments")
    results: Mapped[List["Result"]] = relationship("Result", back_populates="assignment")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("exams.id"), nullable=True
    )
    assignment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("assignments.id"), nullable=True
    )
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)

    exam: Mapped[Optional["Exam"]] = relationship("Exam", back_populates="results")
    assignment: Mapped[Optional["Assignment"]] = relationship(
        "Assignment", back_populates="results"
    )
    student: Mapped["Student"] = relationship("Student", back_populates="results")


class Attendance(Base):
    __tablename__ = "attendances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="present")
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id"), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="attendances")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="attendances")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    class_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("classes.id"), nullable=True
    )

    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="events")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    class_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("classes.id"), nullable=True
    )

    class_: Mapped[Optional["Class"]] = relationship("Class", back_populates="announcements")


# ── SchoolSync added features ────────────────────────────────────────────────
class StudyTask(Base):
    """Student revision/planning task, separate from teacher-issued assignments."""
    __tablename__ = "study_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    notes: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    subject: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    priority: Mapped[str] = mapped_column(String(12), nullable=False, default="normal")
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    student: Mapped["Student"] = relationship("Student")


class LibraryBook(Base):
    """Catalogue entry with a count of available and total copies."""
    __tablename__ = "library_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(180), nullable=False, default="Unknown")
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    loans: Mapped[List["LibraryLoan"]] = relationship("LibraryLoan", back_populates="book")


class LibraryLoan(Base):
    """Tracks a book copy loaned to a student and its return date."""
    __tablename__ = "library_loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("library_books.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    book: Mapped["LibraryBook"] = relationship("LibraryBook", back_populates="loans")
    student: Mapped["Student"] = relationship("Student")


class AppUser(Base):
    """Local SchoolSync account; passwords are stored only as Argon2 hashes."""
    __tablename__ = "app_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    profile_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DashboardPreference(Base):
    __tablename__ = "dashboard_preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="light")
    widgets: Mapped[str] = mapped_column(String(500), nullable=False, default="stats,attendance,planner,announcements")

class PasswordResetToken(Base):
    """Stores only a hash of a short-lived, single-use password reset token."""
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

