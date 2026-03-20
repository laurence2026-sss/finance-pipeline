CREATE TABLE IF NOT EXISTS restaurants (
  id          INTEGER PRIMARY KEY,
  name        TEXT    NOT NULL,
  category    TEXT    NOT NULL,
  sub         TEXT    NOT NULL,
  lat         REAL,
  lng         REAL,
  rating      REAL,
  price       TEXT,
  description TEXT,
  platforms   TEXT,
  img         TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
