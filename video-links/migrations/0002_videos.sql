-- Per-recipient videos live in R2 (videos/{id}.mp4). NULL = no video uploaded yet.
ALTER TABLE recipients ADD COLUMN video_at TEXT;

-- Player events sent from the video page: 0 = pressed play, 25/50/75 = progress, 100 = watched to the end.
CREATE TABLE watch_events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  recipient_id  TEXT NOT NULL,
  at            TEXT NOT NULL,    -- UTC ISO
  progress      INTEGER NOT NULL
);

CREATE INDEX idx_watch_events_recipient ON watch_events (recipient_id, progress);
