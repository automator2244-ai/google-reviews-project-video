CREATE TABLE recipients (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  phone       TEXT,
  note        TEXT,
  target_url  TEXT,               -- optional: a different video for this recipient
  created_at  TEXT NOT NULL       -- UTC ISO
);

CREATE TABLE clicks (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  recipient_id  TEXT NOT NULL,
  clicked_at    TEXT NOT NULL,    -- UTC ISO
  user_agent    TEXT,
  ip_hash       TEXT,
  country       TEXT,
  is_bot        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_clicks_recipient ON clicks (recipient_id, is_bot);

CREATE TABLE login_attempts (
  ip_hash  TEXT NOT NULL,
  ts       INTEGER NOT NULL       -- unix ms
);

CREATE INDEX idx_login_attempts ON login_attempts (ip_hash, ts);
