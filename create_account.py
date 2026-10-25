"""Create a local SchoolSync login linked to an existing profile.
Run interactively: python create_account.py
"""
import asyncio
import getpass
import selectors
from sqlalchemy import select
from app.database import Base, engine, AsyncSessionLocal
from app.models import AppUser, Admin, Teacher, Student, Parent
from app.security import hash_password

MODELS = {"admin": Admin, "teacher": Teacher, "student": Student, "parent": Parent}

async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        username = input("Login username: ").strip()
        if not username or len(username) > 80:
            print("Username must contain 1–80 characters."); return
        if (await db.execute(select(AppUser).where(AppUser.username.ilike(username)))).scalar_one_or_none():
            print("That username already exists."); return
        role = input("Role (admin/teacher/student/parent): ").strip().lower()
        if role not in MODELS:
            print("Unknown role."); return
        profile_id_text = input("Linked profile ID (blank for an unlinked admin): ").strip()
        profile_id = int(profile_id_text) if profile_id_text else None
        if role != "admin" and profile_id is None:
            print("Teacher/student/parent accounts must be linked to a profile."); return
        if profile_id is not None and not await db.get(MODELS[role], profile_id):
            print(f"No {role} profile found with ID {profile_id}."); return
        password = getpass.getpass("Password (12+ characters): ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords did not match."); return
        try: password_hash = hash_password(password)
        except ValueError as exc:
            print(exc); return
        db.add(AppUser(username=username, role=role, profile_id=profile_id, password_hash=password_hash, is_active=True))
        await db.commit()
        print(f"Created {role} account '{username}'. The password was not displayed or saved as plain text.")

if __name__ == "__main__":
    # Selector loop avoids the ProactorEventLoop incompatibility on some Windows + psycopg setups.
    asyncio.run(create(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
