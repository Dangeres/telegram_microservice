CREATE TABLE IF NOT EXISTS migration
(
    id integer PRIMARY KEY NOT NULL,
    migration_name VARCHAR(255) NOT NULL UNIQUE
);