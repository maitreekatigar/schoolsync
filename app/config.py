"""
config.py — App settings (converted from settings.ts)
"""
from pydantic_settings import BaseSettings
from typing import Dict, List


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://user:password@localhost:5432/schoolsync"
    direct_url: str = "postgresql+psycopg://user:password@localhost:5432/schoolsync"
    session_secret: str = ""
    session_https_only: bool = False
    allowed_hosts: list[str] = ["127.0.0.1", "localhost", "testserver"]
    cors_origins: list[str] = ["http://127.0.0.1:8000", "http://localhost:8000"]
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_jwt_issuer: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_starttls: bool = True
    app_base_url: str = "http://127.0.0.1:8000"
    items_per_page: int = 10
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()

# Equivalent of routeAccessMap from settings.ts
ROUTE_ACCESS_MAP: Dict[str, List[str]] = {
    "/admin": ["admin"],
    "/student": ["student"],
    "/teacher": ["teacher"],
    "/parent": ["parent"],
    "/list/teachers": ["admin", "teacher"],
    "/list/students": ["admin", "teacher"],
    "/list/parents": ["admin", "teacher"],
    "/list/subjects": ["admin"],
    "/list/classes": ["admin", "teacher"],
    "/list/meeting": ["admin", "teacher", "parent"],
    "/list/message": ["admin", "teacher", "student", "parent"],
    "/list/exams": ["admin", "teacher", "student", "parent"],
    "/list/assignments": ["admin", "teacher", "student", "parent"],
    "/list/results": ["admin", "teacher", "student", "parent"],
    "/list/attendance": ["admin", "teacher", "student", "parent"],
    "/list/events": ["admin", "teacher", "student", "parent"],
    "/list/announcements": ["admin", "teacher", "student", "parent"],
}
