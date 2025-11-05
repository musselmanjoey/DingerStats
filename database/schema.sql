-- DingerStats Database Schema
-- Stores YouTube videos and game analysis results

CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    published_at TEXT,
    channel_id TEXT,
    playlist_id TEXT,
    duration TEXT,
    thumbnail_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    player_a TEXT,  -- Primary: Player name (e.g., "Dennis", "Nick")
    player_b TEXT,  -- Primary: Player name
    team_a TEXT,    -- Secondary: Character team name (e.g., "Daisy Cupids")
    team_b TEXT,    -- Secondary: Character team name
    score_a INTEGER,
    score_b INTEGER,
    winner TEXT,    -- Player name who won
    raw_response TEXT,  -- Store full Gemini response
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence TEXT,  -- high, medium, low
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending, processing, completed, failed
    error_message TEXT,
    attempt_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_playlist ON videos(playlist_id);
CREATE INDEX IF NOT EXISTS idx_game_results_video ON game_results(video_id);
CREATE INDEX IF NOT EXISTS idx_processing_status ON processing_log(status);
