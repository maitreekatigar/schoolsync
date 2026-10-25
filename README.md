# SchoolSync — upgraded local-first edition

SchoolSync is a server-rendered FastAPI + PostgreSQL school-management app. HTML templates and CSS provide the UI; a small JavaScript file handles calendar filtering. It builds on the existing SchoolSync Python project.

## What is included

- Local username/password sign-in using Argon2id password hashes, signed sessions, sign-out, and server-side role checks (`admin`, `teacher`, `student`, `parent`). There is no public self-registration.
- CSRF tokens on state-changing website forms; login session is rotated after successful authentication; session cookies are `HttpOnly` via Starlette's session middleware.
- Role-filtered dashboard, student progress and report views, linked parent portal, attendance register with present/absent/late/excused states, planner month calendar + date-filtered task list, themes and saved dashboard widgets, teacher hub, and library catalogue/loans.
- Existing JSON API routers remain in place and continue to use the project's Clerk JWT dependencies where configured.
- SQL migration script, account provisioning helper, basic tests, and deployment checklist.

## Important scope and safety notes

**This is still a local development package, not a security-audited production release. Keep it bound to your own computer and use synthetic data.** It has not been tested against your actual PostgreSQL database in this environment. Existing deployments need the migration below. The old schema has no unique constraint for attendance by student/lesson/date, and this UI upserts that combination by lookup; concurrent writes could race. Some school workflows (timetable authoring, grading workflows, assignment submission/review, notification delivery, account recovery, audit trail, password reset, MFA, rate limiting, and formal parent verification) remain future work. Do not put real student information online until a qualified review and end-to-end tests are completed.

The local account table links an account to an existing profile ID. Admins must provision accounts deliberately; do not share logins. Existing Clerk API authentication and this local website session are separate systems.

## Windows setup

Use Python 3.12 or newer (Python 3.12 is a good choice with current database drivers) and a local PostgreSQL database named `schoolsync`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Set `DATABASE_URL` to your local PostgreSQL connection and set `SESSION_SECRET` to a unique random secret. Never share `.env` or put it in a ZIP/repository. Generate a secret in PowerShell, then copy the printed value into `.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep `DEBUG=true`, `SESSION_HTTPS_ONLY=false`, and the default localhost-only `ALLOWED_HOSTS` for local development. Do not change host/CORS settings to expose the app to your network or internet as a shortcut.

### Apply schema changes to your existing database

Back up the local database first. If this is a brand-new empty database, run the project seed script once first to create the original school tables (the seed script is not idempotent). The migration script is additive and targets PostgreSQL. In pgAdmin, open Query Tool for the `schoolsync` database, open `migrations/001_security_attendance_planner.sql`, review it, and execute it. Alternatively use `psql` if installed. It creates the local accounts/preferences tables and adds planner/attendance fields. `Base.metadata.create_all()` does not add columns to existing tables, so do not skip this migration.

### Create your first login

Run this only after the migration. The command creates an account for an existing profile; it never stores plain-text passwords.

```powershell
python create_account.py
```

Enter `admin` as the role and leave the linked profile ID blank for an administrator. For a teacher/student/parent account, link the correct matching profile ID. The seed data's profile IDs can vary, so inspect the IDs in pgAdmin first. Use a unique password with at least 12 characters. If you have not seeded your database yet, follow the existing seed script's guidance; the seed script is intended for a fresh database and is not idempotent.

### Start locally

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/login`. Sign in with the account you just created. Keep the `127.0.0.1` host binding: it is local to your computer. API docs are available at `/docs` while `DEBUG=true`.

If you see a psycopg ProactorEventLoop error while running the seed/account script on Windows, use the `SelectorEventLoop` workaround already included in `create_account.py`; use Python 3.12 if your current Python/driver combination has issues.

## Tests

```powershell
python -m pytest -q
```

These tests cover password hashing only; they are not a substitute for route authorization, CSRF, migration, and database integration tests. Run a full test pass against a disposable local database before relying on the application.

## Production preparation checklist (not yet deployment-ready)

Before any deployment: obtain a security review; complete route-by-route authorization tests for all JSON API endpoints; add audit logging, rate limits, account recovery and password reset, MFA for staff, secure account linking/invitation, strict CSP/security headers, HTTPS-only cookies, secrets management, backup/restore drills, monitoring, migrations in CI, and tested least-privilege database credentials. Use a managed PostgreSQL service, a unique production `SESSION_SECRET`, `DEBUG=false`, `SESSION_HTTPS_ONLY=true`, explicit HTTPS CORS origins and trusted hosts, and a reverse proxy that enforces HTTPS. Never use the sample credentials or real school data during early testing. Do not deploy until these items are completed.
