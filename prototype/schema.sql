CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL
);

CREATE TABLE meme (
  meme_id INTEGER PRIMARY KEY,
  id TEXT,
  url TEXT,
  date_of_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id) REFERENCES user(id)
);

CREATE TABLE like (
  id TEXT,
  meme_id INT,
  PRIMARY KEY (id, meme_id),
  FOREIGN KEY (id) REFERENCES user(id),
  FOREIGN KEY (meme_id) REFERENCES meme(meme_id)
)