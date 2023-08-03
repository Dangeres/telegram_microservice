CREATE TABLE IF NOT EXISTS message_secret
(
    id TEXT PRIMARY KEY NOT NULL,
    secret TEXT NOT NULL,
	token_service TEXT NOT NULL,
    dt timestamp
);

CREATE TABLE IF NOT EXISTS message_result
(
    id TEXT PRIMARY KEY NOT NULL,
    message_id integer,
    sender integer NOT NULL,
    error TEXT,
    dt timestamp
);