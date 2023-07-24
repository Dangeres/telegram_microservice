CREATE TABLE IF NOT EXISTS tokens
(
    id TEXT PRIMARY KEY NOT NULL,
    create_dt timestamp,
    untill_dt timestamp
);