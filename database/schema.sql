CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_registration (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    discord_id TEXT NOT NULL,
    real_name TEXT NOT NULL,
    in_game_name TEXT NOT NULL,
    birthday DATE NOT NULL,
    uuid TEXT NOT NULL,
    current_rank TEXT NOT NULL,
    games_played TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS tiktok_users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_user_id INTEGER,
  tiktok_username TEXT,
  role_id INTEGER
);