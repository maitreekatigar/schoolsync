"""
seed.py — Database seed script
Converted from: prisma/seed.ts + src/lib/data.ts

Run with:
    python seed.py
"""
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base, AsyncSessionLocal
from app.models import (
    Admin, Grade, Subject, Parent, Teacher, Class,
    Student, Lesson, Exam, Assignment, Result,
    Attendance, Event, Announcement, UserSex, Day
)


async def seed():
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ── Grades ───────────────────────────────────────────────────────────
        grades = [Grade(level=i) for i in range(1, 9)]
        db.add_all(grades)
        await db.flush()

        # ── Subjects ─────────────────────────────────────────────────────────
        subject_names = [
            "Math", "English", "Physics", "Chemistry", "Biology",
            "History", "Geography", "Art", "Music", "Literature"
        ]
        subjects = [Subject(name=name) for name in subject_names]
        db.add_all(subjects)
        await db.flush()

        # ── Admin ─────────────────────────────────────────────────────────────
        admin = Admin(
            username="admin",
            name="Admin",
            surname="User",
            email="admin@schoolsync.com",
        )
        db.add(admin)
        await db.flush()

        # ── Parents ───────────────────────────────────────────────────────────
        parents_data = [
            {"username": "johndoe", "name": "John", "surname": "Doe", "email": "john@doe.com", "phone": "1234567890", "address": "123 Main St, Anytown, USA"},
            {"username": "janedoe", "name": "Jane", "surname": "Doe", "email": "jane@doe.com", "phone": "1234567891", "address": "123 Main St, Anytown, USA"},
            {"username": "mikegeller", "name": "Mike", "surname": "Geller", "email": "mike@geller.com", "phone": "1234567892", "address": "123 Main St, Anytown, USA"},
            {"username": "jayfrench", "name": "Jay", "surname": "French", "email": "jay@gmail.com", "phone": "1234567893", "address": "123 Main St, Anytown, USA"},
            {"username": "janesmith", "name": "Jane", "surname": "Smith", "email": "janesmith@gmail.com", "phone": "1234567894", "address": "123 Main St, Anytown, USA"},
        ]
        parents = [Parent(**p) for p in parents_data]
        db.add_all(parents)
        await db.flush()

        # ── Teachers ──────────────────────────────────────────────────────────
        teachers_data = [
            {"username": "johndoe_t", "name": "John", "surname": "Doe", "email": "johnt@doe.com", "phone": "9876543210", "address": "123 Main St", "blood_type": "A+", "sex": UserSex.MALE, "birthday": datetime(1985, 5, 15)},
            {"username": "janedoe_t", "name": "Jane", "surname": "Doe", "email": "janet@doe.com", "phone": "9876543211", "address": "123 Main St", "blood_type": "B+", "sex": UserSex.FEMALE, "birthday": datetime(1988, 3, 22)},
            {"username": "mikegeller_t", "name": "Mike", "surname": "Geller", "email": "miket@geller.com", "phone": "9876543212", "address": "123 Main St", "blood_type": "O+", "sex": UserSex.MALE, "birthday": datetime(1982, 7, 10)},
            {"username": "jayfrench_t", "name": "Jay", "surname": "French", "email": "jayt@gmail.com", "phone": "9876543213", "address": "123 Main St", "blood_type": "AB+", "sex": UserSex.MALE, "birthday": datetime(1979, 11, 5)},
            {"username": "janesmith_t", "name": "Jane", "surname": "Smith", "email": "janest@gmail.com", "phone": "9876543214", "address": "123 Main St", "blood_type": "A-", "sex": UserSex.FEMALE, "birthday": datetime(1990, 1, 28)},
        ]
        teachers = [Teacher(**t) for t in teachers_data]
        # Assign subjects
        teachers[0].subjects = [subjects[0], subjects[1]]  # Math, English
        teachers[1].subjects = [subjects[2], subjects[3]]  # Physics, Chemistry
        teachers[2].subjects = [subjects[4]]               # Biology
        teachers[3].subjects = [subjects[5]]               # History
        teachers[4].subjects = [subjects[8], subjects[5]]  # Music, History
        db.add_all(teachers)
        await db.flush()

        # ── Classes ───────────────────────────────────────────────────────────
        classes_data = [
            {"name": "1A", "capacity": 20, "grade_id": grades[0].id, "supervisor_id": teachers[0].id},
            {"name": "2B", "capacity": 22, "grade_id": grades[1].id, "supervisor_id": teachers[1].id},
            {"name": "3C", "capacity": 20, "grade_id": grades[2].id, "supervisor_id": teachers[2].id},
            {"name": "4B", "capacity": 18, "grade_id": grades[3].id, "supervisor_id": teachers[3].id},
            {"name": "5A", "capacity": 16, "grade_id": grades[4].id, "supervisor_id": teachers[4].id},
        ]
        classes = [Class(**c) for c in classes_data]
        db.add_all(classes)
        await db.flush()

        # ── Students ──────────────────────────────────────────────────────────
        students_data = [
            {"username": "student1", "name": "Sarah", "surname": "Brewer", "address": "456 Oak Ave", "blood_type": "O+", "sex": UserSex.FEMALE, "birthday": datetime(2010, 3, 12), "parent_id": parents[0].id, "class_id": classes[0].id, "grade_id": grades[0].id},
            {"username": "student2", "name": "Cecilia", "surname": "Bradley", "address": "789 Pine St", "blood_type": "A+", "sex": UserSex.FEMALE, "birthday": datetime(2011, 6, 22), "parent_id": parents[1].id, "class_id": classes[1].id, "grade_id": grades[1].id},
            {"username": "student3", "name": "Fanny", "surname": "Caldwell", "address": "321 Elm St", "blood_type": "B-", "sex": UserSex.FEMALE, "birthday": datetime(2012, 9, 8), "parent_id": parents[2].id, "class_id": classes[2].id, "grade_id": grades[2].id},
            {"username": "student4", "name": "Mollie", "surname": "Fitzgerald", "address": "654 Maple Dr", "blood_type": "AB+", "sex": UserSex.FEMALE, "birthday": datetime(2013, 1, 18), "parent_id": parents[3].id, "class_id": classes[3].id, "grade_id": grades[3].id},
            {"username": "student5", "name": "Mable", "surname": "Harvey", "address": "987 Cedar Ln", "blood_type": "O-", "sex": UserSex.FEMALE, "birthday": datetime(2014, 4, 25), "parent_id": parents[4].id, "class_id": classes[4].id, "grade_id": grades[4].id},
        ]
        students = [Student(**s) for s in students_data]
        db.add_all(students)
        await db.flush()

        # ── Lessons ───────────────────────────────────────────────────────────
        lesson = Lesson(
            name="Math - 1A Monday",
            day=Day.MONDAY,
            start_time=datetime(2024, 11, 18, 8, 0),
            end_time=datetime(2024, 11, 18, 8, 45),
            subject_id=subjects[0].id,
            class_id=classes[0].id,
            teacher_id=teachers[0].id,
        )
        db.add(lesson)
        await db.flush()

        # ── Events ────────────────────────────────────────────────────────────
        events_seed = [
            Event(title="Annual Sports Day", description="School-wide sports competition", start_time=datetime(2025, 3, 15, 9, 0), end_time=datetime(2025, 3, 15, 16, 0)),
            Event(title="Science Fair", description="Students present science projects", start_time=datetime(2025, 2, 20, 10, 0), end_time=datetime(2025, 2, 20, 14, 0), class_id=classes[0].id),
            Event(title="Lake Trip", description="Nature excursion", start_time=datetime(2025, 4, 10, 10, 0), end_time=datetime(2025, 4, 10, 16, 0), class_id=classes[1].id),
        ]
        db.add_all(events_seed)

        # ── Announcements ─────────────────────────────────────────────────────
        announcements_seed = [
            Announcement(title="About 4A Math Test", description="Math test scheduled for next Monday", date=datetime(2025, 1, 1), class_id=classes[3].id),
            Announcement(title="About 3C Science Project", description="Submit by end of term", date=datetime(2025, 1, 2), class_id=classes[2].id),
            Announcement(title="School Holiday Notice", description="School closed on Nov 15", date=datetime(2024, 11, 1)),
        ]
        db.add_all(announcements_seed)

        await db.commit()
        print("✅ Database seeded successfully!")
        print(f"   Grades: {len(grades)}")
        print(f"   Subjects: {len(subjects)}")
        print(f"   Parents: {len(parents)}")
        print(f"   Teachers: {len(teachers)}")
        print(f"   Classes: {len(classes)}")
        print(f"   Students: {len(students)}")


if __name__ == "__main__":
    asyncio.run(seed())
