CREATE TABLE IF NOT EXISTS message_secret
(
    token TEXT PRIMARY KEY NOT NULL,
    secret TEXT NOT NULL,
    dt timestamp
);

CREATE TABLE IF NOT EXISTS message_result
(
    token TEXT PRIMARY KEY NOT NULL,
    message_id integer,
    sender integer NOT NULL,
    error TEXT
);