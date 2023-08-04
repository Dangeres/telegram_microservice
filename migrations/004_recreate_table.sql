DROP TABLE IF EXISTS message_result;

CREATE TABLE IF NOT EXISTS message_result
(
    id TEXT PRIMARY KEY NOT NULL,
    message_id integer,
    sender bigint,
    error TEXT,
    dt timestamp
);