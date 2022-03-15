DROP TABLE IF exists urls;
DROP TABLE IF exists user;
DROP TABLE IF exists api_keys;

CREATE TABLE urls (
  id integer PRIMARY KEY NOT NULL,
  timestamp datetime default current_timestamp,
  expiry datetime,
  url text,
  shorturl text UNIQUE,
  views INTEGER default 0
);

CREATE TABLE user (
  id integer PRIMARY KEY NOT NULL,
  username text UNIQUE,
  password text,
  created datetime default current_timestamp
);

CREATE table api_keys (
  key text UNIQUE NOT NULL,
  environment text,
  created datetime default current_timestamp,
  userId INTEGER NOT NULL,
  FOREIGN KEY(userId) REFERENCES user(id)
)

INSERT INTO user (username, password) VALUES ('user', 'test')
INSERT INTO api_keys (key, environment, userId) VALUES ('abc123', 'development', 1);