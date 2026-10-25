"""SchoolSync: local-first FastAPI school management application."""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.routers import (teachers, students, parents, classes, lessons, exams, assignments,
                         results, attendance, events, announcements, dashboard, subjects)
from app.routers import web

BASE_DIR = Path(__file__).resolve().parent
if len(settings.session_secret) < 32 or settings.session_secret.startswith("replace-with-"):
    raise RuntimeError("Set SESSION_SECRET to a unique random value of at least 32 characters in .env before starting SchoolSync")

app = FastAPI(title="SchoolSync", description="Local-first school management platform", version="3.0.0", docs_url="/docs" if settings.debug else None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, session_cookie="schoolsync_session", same_site="lax", https_only=settings.session_https_only, max_age=60*60*8)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET","POST","PATCH","DELETE"], allow_headers=["Authorization","Content-Type"])
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
for router in (teachers.router, students.router, parents.router, classes.router, lessons.router, exams.router, assignments.router, results.router, attendance.router, events.router, announcements.router, dashboard.router, subjects.router, web.router):
    app.include_router(router)

@app.get("/health", tags=["Health"])
async def health():
    return {"status":"ok", "environment":"local" if settings.debug else "production"}
