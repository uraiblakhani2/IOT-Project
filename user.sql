BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "user" (
	"user_id"	INTEGER,
	"name"	TEXT,
	"temp_threshold"	INTEGER,
	"humidity_threshold"	INTEGER,
	"light_threshold"	INTEGER,
	PRIMARY KEY("user_id")
);
COMMIT;
