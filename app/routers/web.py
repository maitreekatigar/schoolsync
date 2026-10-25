"""Authenticated server-rendered SchoolSync workspace (local-first)."""
from datetime import date, datetime, timedelta
from pathlib import Path
import secrets
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import (AppUser, DashboardPreference, Admin, Student, Teacher, Parent, Class, Subject,
                        StudyTask, Attendance, Lesson, Result, Assignment, Exam, Event,
                        Announcement, LibraryBook, LibraryLoan, PasswordResetToken)
from app.security import verify_password, hash_password

router = APIRouter(tags=["SchoolSync Web"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
ROLES = {"admin", "teacher", "student", "parent"}

def csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token

def check_csrf(request: Request, token: str):
    expected = request.session.get("csrf_token", "")
    if not expected or not secrets.compare_digest(expected, token):
        raise HTTPException(status_code=403, detail="Form expired. Reload the page and try again.")

def page(request: Request, name: str, **context):
    context.update({"user": request.session.get("user"), "csrf_token": csrf(request),
                    "theme": request.session.get("theme", "light"), "request": request})
    return templates.TemplateResponse(request=request, name=name, context=context)

async def current_user(request: Request, db: AsyncSession = Depends(get_db)) -> AppUser:
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = await db.get(AppUser, uid)
    if not user or not user.is_active:
        request.session.clear()
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

def roles(*allowed):
    async def guard(user: AppUser = Depends(current_user)):
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Your account role cannot access this page.")
        return user
    return guard

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return page(request, "login.html", error=None)

@router.post("/login", include_in_schema=False)
async def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(...), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    result = await db.execute(select(AppUser).where(func.lower(AppUser.username) == username.strip().lower()))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return page(request, "login.html", error="Sign-in failed. Check your username and password.")
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["user"] = {"username": user.username, "role": user.role}
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    return RedirectResponse("/", status_code=303)



def _send_reset_email(to_email: str, reset_url: str):
    if not (settings.smtp_host and settings.smtp_username and settings.smtp_password and settings.smtp_from_email):
        raise RuntimeError("SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL in .env.")
    msg = EmailMessage()
    msg["Subject"] = "Reset your SchoolSync password"
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.set_content(f"Someone requested a SchoolSync password reset. This link expires in 30 minutes and can be used once:\n\n{reset_url}\n\nIf you did not request this, ignore this email.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        server.ehlo()
        if settings.smtp_starttls:
            server.starttls()
            server.ehlo()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)

def _profile_email(user, db):
    # Email is kept on the existing school profile, not duplicated on app_users.
    return None

@router.get("/forgot-password", response_class=HTMLResponse, include_in_schema=False)
async def forgot_password_page(request: Request):
    return page(request, "forgot_password.html", message=None, error=None)

@router.post("/forgot-password", response_class=HTMLResponse, include_in_schema=False)
async def forgot_password(request: Request, username: str = Form(...), csrf_token: str = Form(...), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    user = (await db.execute(select(AppUser).where(func.lower(AppUser.username) == username.strip().lower()))).scalar_one_or_none()
    # Always use a generic response to avoid revealing account existence.
    if user and user.is_active:
        profile_model = {"student": Student, "teacher": Teacher, "parent": Parent, "admin": Admin}.get(user.role)
        email = None
        if profile_model and user.profile_id:
            profile = await db.get(profile_model, user.profile_id)
            email = getattr(profile, "email", None) if profile else None
        if email:
            raw = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw.encode()).hexdigest()
            now = datetime.utcnow()
            await db.execute(__import__("sqlalchemy").delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)))
            db.add(PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=now + timedelta(minutes=30)))
            await db.commit()
            url = f"{settings.app_base_url.rstrip('/')}/reset-password?token={raw}"
            try:
                await asyncio.to_thread(_send_reset_email, email, url)
            except Exception:
                # Don't leak whether the username exists; log only configuration/runtime error server-side.
                import logging
                logging.getLogger("schoolsync.password_reset").exception("Could not send password reset email")
    return page(request, "forgot_password.html", message="If that username has a linked email address, a password-reset link will be sent shortly.", error=None)

@router.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
async def reset_password_page(request: Request, token: str = ""):
    return page(request, "reset_password.html", token=token, error=None, success=None)

@router.post("/reset-password", response_class=HTMLResponse, include_in_schema=False)
async def reset_password(request: Request, token: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), csrf_token: str = Form(...), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    if len(password) < 12:
        return page(request, "reset_password.html", token=token, error="Use a password with at least 12 characters.", success=None)
    if password != confirm_password:
        return page(request, "reset_password.html", token=token, error="Passwords do not match.", success=None)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    reset = (await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash, PasswordResetToken.used_at.is_(None), PasswordResetToken.expires_at > datetime.utcnow()))).scalar_one_or_none()
    if not reset:
        return page(request, "reset_password.html", token="", error="This reset link is invalid or expired. Request a new one.", success=None)
    user = await db.get(AppUser, reset.user_id)
    if not user or not user.is_active:
        return page(request, "reset_password.html", token="", error="This reset link is invalid or expired. Request a new one.", success=None)
    user.password_hash = hash_password(password)
    reset.used_at = datetime.utcnow()
    await db.execute(__import__("sqlalchemy").delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id, PasswordResetToken.id != reset.id))
    await db.commit()
    return RedirectResponse("/login?reset=1", status_code=303)

@router.post("/logout", include_in_schema=False)
async def logout(request: Request, csrf_token: str = Form(...)):
    check_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request, user: AppUser = Depends(current_user), db: AsyncSession = Depends(get_db)):
    pref = (await db.execute(select(DashboardPreference).where(DashboardPreference.user_id == user.id))).scalar_one_or_none()
    if pref:
        request.session["theme"] = pref.theme
    widgets = (pref.widgets.split(",") if pref else ["stats", "attendance", "planner", "announcements"])
    stats = {}
    if user.role in ("admin", "teacher"):
        for key, model in (("students", Student), ("teachers", Teacher), ("classes", Class), ("subjects", Subject)):
            stats[key] = (await db.execute(select(func.count()).select_from(model))).scalar_one()
    tasks_q = select(StudyTask).order_by(StudyTask.due_date).limit(8)
    if user.role == "parent":
        parent = (await db.execute(select(Parent).options(selectinload(Parent.students).selectinload(Student.class_), selectinload(Parent.students).selectinload(Student.grade)).where(Parent.id == user.profile_id))).scalar_one_or_none() if user.profile_id else None
        tasks_q = tasks_q.where(StudyTask.student_id.in_([x.id for x in parent.students] if parent else [-1]))
    if user.role == "student":
        student = await db.get(Student, user.profile_id) if user.profile_id else None
        tasks_q = tasks_q.where(StudyTask.student_id == (student.id if student else -1))
    tasks = (await db.execute(tasks_q)).scalars().all()
    announcements = (await db.execute(select(Announcement).order_by(desc(Announcement.date)).limit(5))).scalars().all()
    attendance_count = (await db.execute(select(func.count()).select_from(Attendance))).scalar_one() if user.role in ("admin", "teacher") else 0
    return page(request, "dashboard.html", stats=stats, tasks=tasks, announcements=announcements,
                widgets=widgets, attendance_count=attendance_count, today=date.today(), role=user.role)

@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request, user: AppUser = Depends(current_user), db: AsyncSession = Depends(get_db)):
    pref = (await db.execute(select(DashboardPreference).where(DashboardPreference.user_id == user.id))).scalar_one_or_none()
    return page(request, "settings.html", preference=pref, all_widgets=[("stats","School statistics"),("attendance","Attendance snapshot"),("planner","Study planner"),("announcements","Announcements")])

@router.post("/settings", include_in_schema=False)
async def save_settings(request: Request, csrf_token: str = Form(...), theme: str = Form("light"), widgets: list[str] = Form([]), user: AppUser = Depends(current_user), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    if theme not in ("light", "dark", "system"): raise HTTPException(400, "Invalid theme")
    allowed = {"stats", "attendance", "planner", "announcements"}
    chosen = [x for x in widgets if x in allowed]
    pref = (await db.execute(select(DashboardPreference).where(DashboardPreference.user_id == user.id))).scalar_one_or_none()
    if not pref:
        pref = DashboardPreference(user_id=user.id, theme=theme, widgets=",".join(chosen)); db.add(pref)
    else: pref.theme, pref.widgets = theme, ",".join(chosen)
    request.session["theme"] = theme
    await db.commit()
    return RedirectResponse("/settings?saved=1", status_code=303)

@router.get("/attendance", response_class=HTMLResponse, include_in_schema=False)
async def attendance_page(request: Request, user: AppUser = Depends(roles("admin", "teacher", "student", "parent")), db: AsyncSession = Depends(get_db)):
    students = []
    rows = []
    lessons = []
    if user.role in ("admin", "teacher"):
        lesson_query = select(Lesson).order_by(Lesson.name)
        if user.role == "teacher": lesson_query = lesson_query.where(Lesson.teacher_id == user.profile_id)
        lessons = (await db.execute(lesson_query)).scalars().all()
        if user.role == "teacher":
            class_ids = (await db.execute(select(Lesson.class_id).where(Lesson.teacher_id == user.profile_id).distinct())).scalars().all()
            students = (await db.execute(select(Student).options(selectinload(Student.class_)).where(Student.class_id.in_(class_ids or [-1])).order_by(Student.surname, Student.name))).scalars().all()
            lesson_ids = [x.id for x in lessons]
            rows = (await db.execute(select(Attendance).options(selectinload(Attendance.student), selectinload(Attendance.lesson)).where(Attendance.lesson_id.in_(lesson_ids or [-1])).order_by(desc(Attendance.date)).limit(150))).scalars().all()
        else:
            students = (await db.execute(select(Student).options(selectinload(Student.class_)).order_by(Student.surname, Student.name))).scalars().all()
            rows = (await db.execute(select(Attendance).options(selectinload(Attendance.student), selectinload(Attendance.lesson)).order_by(desc(Attendance.date)).limit(150))).scalars().all()
    else:
        student = await db.get(Student, user.profile_id) if user.role == "student" else None
        if user.role == "parent":
            parent = (await db.execute(select(Parent).options(selectinload(Parent.students).selectinload(Student.class_), selectinload(Parent.students).selectinload(Student.grade)).where(Parent.id==user.profile_id))).scalar_one_or_none() if user.profile_id else None
            students = list(parent.students) if parent else []
            ids = [s.id for s in students]
        else: ids = [student.id] if student else []
        if ids: rows = (await db.execute(select(Attendance).options(selectinload(Attendance.student), selectinload(Attendance.lesson)).where(Attendance.student_id.in_(ids)).order_by(desc(Attendance.date)).limit(150))).scalars().all()
    return page(request, "attendance.html", students=students, rows=rows, lessons=lessons, today=date.today().isoformat(), can_mark=user.role in ("admin","teacher"))

@router.post("/attendance/mark", include_in_schema=False)
async def mark_attendance(request: Request, csrf_token: str = Form(...), student_id: int = Form(...), lesson_id: int = Form(...), attendance_date: str = Form(...), status_value: str = Form(..., alias="status"), user: AppUser = Depends(roles("admin", "teacher")), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    if status_value not in ("present", "absent", "late", "excused"): raise HTTPException(400, "Invalid attendance status")
    student, lesson = await db.get(Student, student_id), await db.get(Lesson, lesson_id)
    if not student or not lesson: raise HTTPException(400, "Select a valid student and lesson")
    if user.role == "teacher" and (lesson.teacher_id != user.profile_id or student.class_id != lesson.class_id):
        raise HTTPException(403, "Teachers may only mark attendance for their own lessons and classes.")
    try: day = datetime.strptime(attendance_date, "%Y-%m-%d")
    except ValueError: raise HTTPException(400, "Invalid date")
    row = (await db.execute(select(Attendance).where(Attendance.student_id == student_id, Attendance.lesson_id == lesson_id, func.date(Attendance.date) == day.date()))).scalar_one_or_none()
    present = status_value in ("present", "late")
    if row: row.status, row.present, row.date = status_value, present, day
    else: db.add(Attendance(date=day, present=present, status=status_value, student_id=student_id, lesson_id=lesson_id))
    await db.commit()
    return RedirectResponse("/attendance", status_code=303)

@router.get("/planner", response_class=HTMLResponse, include_in_schema=False)
async def planner_page(request: Request, month: str | None = None, user: AppUser = Depends(current_user), db: AsyncSession = Depends(get_db)):
    try: month_start = datetime.strptime(month, "%Y-%m") if month else datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    except ValueError: month_start = datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    query = select(StudyTask).options(selectinload(StudyTask.student)).order_by(StudyTask.due_date)
    if user.role == "student": query = query.where(StudyTask.student_id == (user.profile_id or -1))
    if user.role == "parent":
        parent = (await db.execute(select(Parent).options(selectinload(Parent.students).selectinload(Student.class_), selectinload(Parent.students).selectinload(Student.grade)).where(Parent.id == user.profile_id))).scalar_one_or_none() if user.profile_id else None
        query = query.where(StudyTask.student_id.in_([x.id for x in parent.students] if parent else [-1]))
    tasks = (await db.execute(query)).scalars().all()
    students = (await db.execute(select(Student).order_by(Student.surname, Student.name))).scalars().all() if user.role in ("admin", "teacher") else []
    lessons = (await db.execute(select(Lesson).order_by(Lesson.name))).scalars().all() if user.role in ("admin", "teacher") else []
    import calendar
    cal = calendar.Calendar(firstweekday=0)
    calendar_days = cal.monthdatescalendar(month_start.year, month_start.month)
    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    return page(request, "planner.html", tasks=tasks, students=students, lessons=lessons, month_start=month_start, next_month=next_month, prev_month=prev_month, today=date.today(), calendar_days=calendar_days, can_manage=user.role in ("admin","teacher","student"), user_role=user.role)

@router.post("/planner/tasks", include_in_schema=False)
async def create_task(request: Request, csrf_token: str = Form(...), title: str = Form(...), due_date: str = Form(...), notes: str = Form(""), subject: str = Form("General"), priority: str = Form("normal"), student_id: int | None = Form(None), user: AppUser = Depends(roles("admin", "teacher", "student")), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    if not title.strip() or len(title) > 180: raise HTTPException(400, "Task title is required (180 characters max)")
    if priority not in ("low", "normal", "high"): raise HTTPException(400, "Invalid priority")
    try: due = datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError: raise HTTPException(400, "Invalid due date")
    target = student_id if user.role in ("admin", "teacher") and student_id else user.profile_id
    if user.role == "student" and not user.profile_id: raise HTTPException(403, "Your account is not linked to a student profile")
    if not target: raise HTTPException(400, "Choose a student profile")
    db.add(StudyTask(title=title.strip(), due_date=due, student_id=target, notes=notes.strip()[:1000], subject=subject.strip()[:100] or "General", priority=priority, completed=False))
    await db.commit()
    return RedirectResponse("/planner", status_code=303)

@router.post("/planner/tasks/{task_id}/toggle", include_in_schema=False)
async def toggle_task(request: Request, task_id: int, csrf_token: str = Form(...), user: AppUser = Depends(roles("admin", "student")), db: AsyncSession = Depends(get_db)):
    check_csrf(request, csrf_token)
    task = await db.get(StudyTask, task_id)
    if not task or (user.role == "student" and task.student_id != user.profile_id): raise HTTPException(404, "Task not found")
    task.completed = not task.completed
    await db.commit()
    return RedirectResponse("/planner", status_code=303)

@router.get("/progress", response_class=HTMLResponse, include_in_schema=False)
async def progress(request: Request, user: AppUser = Depends(roles("admin", "teacher")), db: AsyncSession = Depends(get_db)):
    student_query = select(Student).order_by(Student.surname, Student.name)
    if user.role == "teacher":
        class_ids = (await db.execute(select(Lesson.class_id).where(Lesson.teacher_id == user.profile_id).distinct())).scalars().all()
        student_query = student_query.where(Student.class_id.in_(class_ids or [-1]))
    students = (await db.execute(student_query)).scalars().all(); rows=[]
    for student in students:
        scores=(await db.execute(select(Result.score).where(Result.student_id==student.id))).scalars().all()
        ats=(await db.execute(select(Attendance.status).where(Attendance.student_id==student.id))).scalars().all()
        rows.append({"student":student,"average":round(sum(scores)/len(scores),1) if scores else None,"assessments":len(scores),"attendance":round(100*sum(x in ("present","late") for x in ats)/len(ats),1) if ats else None})
    return page(request,"progress.html",rows=rows)

@router.get("/reports", response_class=HTMLResponse, include_in_schema=False)
async def reports(request: Request, student_id: int | None = None, user: AppUser = Depends(roles("admin", "teacher", "parent", "student")), db: AsyncSession = Depends(get_db)):
    students_query = select(Student).options(selectinload(Student.class_), selectinload(Student.grade)).order_by(Student.surname,Student.name)
    if user.role == "teacher":
        class_ids = (await db.execute(select(Lesson.class_id).where(Lesson.teacher_id == user.profile_id).distinct())).scalars().all()
        students_query = students_query.where(Student.class_id.in_(class_ids or [-1]))
    students = (await db.execute(students_query)).scalars().all()
    if user.role == "student":
        student_id = user.profile_id
        students = [s for s in students if s.id == user.profile_id]
    elif user.role == "parent":
        parent = (await db.execute(select(Parent).options(selectinload(Parent.students).selectinload(Student.class_), selectinload(Parent.students).selectinload(Student.grade)).where(Parent.id==user.profile_id))).scalar_one_or_none() if user.profile_id else None
        allowed = [x.id for x in parent.students] if parent else []
        students = [s for s in students if s.id in allowed]
        if student_id not in allowed: student_id = allowed[0] if allowed else None
    student = next((s for s in students if s.id==student_id),None) if student_id else None
    results=[]; total=present=0
    if student:
        for r in (await db.execute(select(Result).options(selectinload(Result.exam), selectinload(Result.assignment)).where(Result.student_id==student.id))).scalars().all():
            label = r.exam.title if r.exam else (r.assignment.title if r.assignment else "Assessment")
            results.append({"label":label,"score":r.score})
        ats=(await db.execute(select(Attendance.status).where(Attendance.student_id==student.id))).scalars().all(); total=len(ats); present=sum(x in ("present","late") for x in ats)
    return page(request,"reports.html",students=students,student=student,results=results,average=round(sum(x["score"] for x in results)/len(results),1) if results else None,attendance_total=total,attendance_present=present,attendance_pct=round(100*present/total,1) if total else None, user_role=user.role)

@router.get("/teacher-hub", response_class=HTMLResponse, include_in_schema=False)
async def teacher_hub(request: Request, teacher_id: int | None = None, user: AppUser = Depends(roles("admin","teacher")), db: AsyncSession = Depends(get_db)):
    teacher = await db.get(Teacher,user.profile_id) if user.role=="teacher" and user.profile_id else (await db.get(Teacher,teacher_id) if user.role=="admin" and teacher_id else None)
    teachers=(await db.execute(select(Teacher).order_by(Teacher.surname,Teacher.name))).scalars().all() if user.role=="admin" else ([teacher] if teacher else [])
    lessons=(await db.execute(select(Lesson).options(selectinload(Lesson.subject),selectinload(Lesson.class_)).where(Lesson.teacher_id==teacher.id).order_by(Lesson.day,Lesson.start_time))).scalars().all() if teacher else []
    return page(request,"teacher_hub.html",teachers=teachers,teacher=teacher,lessons=lessons)

@router.get("/parent-portal", response_class=HTMLResponse, include_in_schema=False)
async def parent_portal(request: Request, user: AppUser = Depends(roles("parent")), db: AsyncSession = Depends(get_db)):
    parent = (await db.execute(select(Parent).options(selectinload(Parent.students).selectinload(Student.class_), selectinload(Parent.students).selectinload(Student.grade)).where(Parent.id==user.profile_id))).scalar_one_or_none() if user.profile_id else None
    children = list(parent.students) if parent else []
    return page(request,"parent_portal.html",parent=parent,children=children)

@router.get("/library", response_class=HTMLResponse, include_in_schema=False)
async def library(request: Request, user: AppUser = Depends(roles("admin","teacher","student","parent")), db: AsyncSession = Depends(get_db)):
    books=(await db.execute(select(LibraryBook).order_by(LibraryBook.title))).scalars().all()
    loans=(await db.execute(select(LibraryLoan).options(selectinload(LibraryLoan.book),selectinload(LibraryLoan.student)).where(LibraryLoan.returned_at.is_(None)).order_by(LibraryLoan.due_date))).scalars().all() if user.role in ("admin","teacher") else []
    students=(await db.execute(select(Student).order_by(Student.surname,Student.name))).scalars().all() if user.role in ("admin","teacher") else []
    return page(request,"library.html",books=books,loans=loans,students=students,today=date.today(),can_manage=user.role in ("admin","teacher"))

@router.post("/library/books", include_in_schema=False)
async def add_book(request: Request, csrf_token: str = Form(...), title: str = Form(...), author: str = Form(...), copies: int = Form(1), user: AppUser = Depends(roles("admin","teacher")), db: AsyncSession = Depends(get_db)):
    check_csrf(request,csrf_token)
    if not title.strip() or copies<1 or copies>500: raise HTTPException(400,"Enter a title and 1–500 copies")
    db.add(LibraryBook(title=title.strip()[:220],author=author.strip()[:180] or "Unknown",total_copies=copies,available_copies=copies)); await db.commit()
    return RedirectResponse("/library",status_code=303)

@router.post("/library/loans", include_in_schema=False)
async def loan_book(request: Request, csrf_token: str = Form(...), book_id: int = Form(...), student_id: int = Form(...), due_date: str = Form(...), user: AppUser = Depends(roles("admin","teacher")), db: AsyncSession = Depends(get_db)):
    check_csrf(request,csrf_token)
    book = (await db.execute(select(LibraryBook).where(LibraryBook.id == book_id).with_for_update())).scalar_one_or_none()
    student = await db.get(Student, student_id)
    if not book or not student or book.available_copies < 1: raise HTTPException(400,"Book unavailable or student invalid")
    try: due=datetime.strptime(due_date,"%Y-%m-%d")
    except ValueError: raise HTTPException(400,"Invalid due date")
    book.available_copies-=1; db.add(LibraryLoan(book_id=book.id,student_id=student.id,due_date=due)); await db.commit()
    return RedirectResponse("/library",status_code=303)

@router.post("/library/loans/{loan_id}/return", include_in_schema=False)
async def return_book(request: Request, loan_id: int, csrf_token: str = Form(...), user: AppUser = Depends(roles("admin","teacher")), db: AsyncSession = Depends(get_db)):
    check_csrf(request,csrf_token); loan=await db.get(LibraryLoan,loan_id)
    if not loan or loan.returned_at: raise HTTPException(404,"Active loan not found")
    loan.returned_at=datetime.now(); book=await db.get(LibraryBook,loan.book_id)
    if book: book.available_copies=min(book.total_copies,book.available_copies+1)
    await db.commit(); return RedirectResponse("/library",status_code=303)
