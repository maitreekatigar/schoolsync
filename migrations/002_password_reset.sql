-- Additive migration for secure, one-time password reset tokens.
CREATE TABLE IF NOT EXISTS password_reset_tokens (
 id SERIAL PRIMARY KEY,
 user_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
 token_hash VARCHAR(64) UNIQUE NOT NULL,
 expires_at TIMESTAMP NOT NULL,
 used_at TIMESTAMP NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_user_id ON password_reset_tokens(user_id);
