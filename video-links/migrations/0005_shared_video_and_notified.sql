-- Shared videos: a recipient with video_key plays shared/{video_key}.mp4 (one file for many links).
-- NULL = the recipient's own videos/{id}.mp4, as before.
ALTER TABLE recipients ADD COLUMN video_key TEXT;

-- Which viewing milestones were already reported to Bnaya by the summary email (50 = passed half, 100 = to the end).
CREATE TABLE notified (
  recipient_id  TEXT NOT NULL,
  milestone     INTEGER NOT NULL,
  notified_at   TEXT NOT NULL,    -- UTC ISO
  PRIMARY KEY (recipient_id, milestone)
);
