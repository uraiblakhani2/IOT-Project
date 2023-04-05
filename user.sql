BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "user" (
	"user_id"	INTEGER,
	"name"	NUMERIC,
	"temp_threshold"	INTEGER,
	"humidity_threshold"	INTEGER,
	"light_threshold"	INTEGER,
	"picture"	TEXT,
	PRIMARY KEY("user_id")
);
COMMIT;
