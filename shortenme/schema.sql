CREATE TABLE urls (
  id integer PRIMARY KEY NOT NULL,
  timestamp datetime default current_timestamp,
  expiry datetime,
  url text,
  shorturl text UNIQUE,
  views INTEGER default 0
);