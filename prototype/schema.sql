CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL
);

CREATE TABLE meme (
  id TEXT,
  url TEXT,
  PRIMARY KEY (id, url),
  FOREIGN KEY (id) REFERENCES user(id)
);