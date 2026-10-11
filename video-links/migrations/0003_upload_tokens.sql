-- One-hour upload passes, created together with the recipient. Only the SHA-256 of the pass is stored.
CREATE TABLE upload_tokens (
  token_hash    TEXT PRIMARY KEY,
  recipient_id  TEXT NOT NULL,
  expires_at    INTEGER NOT NULL  -- unix ms
);
