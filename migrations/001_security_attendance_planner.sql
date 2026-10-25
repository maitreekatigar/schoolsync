-- Review before applying to an existing local database. Back up first.
-- Safe to re-run with PostgreSQL.
CREATE TABLE IF NOT EXISTS app_users (
 id SERIAL PRIMARY KEY,
 username VARCHAR(80) UNIQUE NOT NULL,
 password_hash VARCHAR(255) NOT NULL,
 role VARCHAR(20) NOT NULL,
 profile_id INTEGER NULL,
 is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_app_users_username ON app_users(username);
CREATE INDEX IF NOT EXISTS ix_app_users_role ON app_users(role);
CREATE TABLE IF NOT EXISTS dashboard_preferences (
 id SERIAL PRIMARY KEY,
 user_id INTEGER UNIQUE NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
 theme VARCHAR(10) NOT NULL DEFAULT 'light',
 widgets VARCHAR(500) NOT NULL DEFAULT 'stats,attendance,planner,announcements'
);
CREATE TABLE IF NOT EXISTS study_tasks (
 id SERIAL PRIMARY KEY,
 title VARCHAR(180) NOT NULL,
 notes VARCHAR(1000) NOT NULL DEFAULT '',
 due_date TIMESTAMP NOT NULL,
 completed BOOLEAN NOT NULL DEFAULT FALSE,
 student_id INTEGER NOT NULL REFERENCES students(id),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS library_books (
 id SERIAL PRIMARY KEY,
 title VARCHAR(220) NOT NULL,
 author VARCHAR(180) NOT NULL DEFAULT 'Unknown',
 total_copies INTEGER NOT NULL DEFAULT 1,
 available_copies INTEGER NOT NULL DEFAULT 1,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_library_books_title ON library_books(title);
CREATE TABLE IF NOT EXISTS library_loans (
 id SERIAL PRIMARY KEY,
 book_id INTEGER NOT NULL REFERENCES library_books(id),
 student_id INTEGER NOT NULL REFERENCES students(id),
 borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 due_date TIMESTAMP NOT NULL,
 returned_at TIMESTAMP NULL
);
ALTER TABLE study_tasks ADD COLUMN IF NOT EXISTS subject VARCHAR(100) NOT NULL DEFAULT 'General';
ALTER TABLE study_tasks ADD COLUMN IF NOT EXISTS priority VARCHAR(12) NOT NULL DEFAULT 'normal';
ALTER TABLE attendances ADD COLUMN IF NOT EXISTS status VARCHAR(12) NOT NULL DEFAULT 'present';
UPDATE attendances SET status = CASE WHEN present THEN 'present' ELSE 'absent' END WHERE status IS NULL OR status = '';
