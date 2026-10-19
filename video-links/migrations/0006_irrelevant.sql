-- Owner can mark a recipient as not relevant from the dashboard (for example after a call).
ALTER TABLE recipients ADD COLUMN irrelevant_at TEXT;
