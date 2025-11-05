# DingerStats - Project Summary

**AI-Powered Mario Baseball Tournament Statistics Tracker**

DingerStats extracts game data from Mario Baseball tournament YouTube videos using AI vision and transcript analysis to create a comprehensive statistics website.

## What It Does

DingerStats automatically analyzes YouTube videos from the "Dinger League" Mario Baseball tournaments (Classic 10 & Season 10) and extracts:

- **Player Information** - Who played in each game
- **Team Composition** - Which Mario characters each player used
- **Game Results** - Final scores and winners
- **Tournament Context** - Game type (Regular Season, Playoffs, Elimination, Finals)
- **Game Summaries** - Key moments and highlights
- **Commentary Highlights** - Memorable commentary moments

This data powers a retro-styled website (authentic 2005 web aesthetics) that displays tournament brackets, player stats, head-to-head records, and more.

## Philosophy

**Multi-Source Data Validation**: Don't trust a single AI model. Get multiple perspectives:

1. **Gemini Visual Analysis** (Primary) - Analyzes video frames for on-screen information
2. **Ollama Transcript Analysis** (Validation) - Analyzes YouTube transcripts using local AI
3. **Manual Review System** - Mark videos as non-games (drafts, analysis videos, etc.)
4. **Version Tracking** - Compare different prompt versions to improve accuracy

This approach ensures data quality through cross-validation rather than blind trust in AI.

## Architecture

### Data Flow

```
YouTube API → Video Metadata → SQLite Database
     ↓
YouTube Videos → AI Analyzers → Game Results → Database
     ↓                  ↓
  Gemini Vision    Ollama Transcript
  (v1, v2...)      (v1, v2...)
     ↓
Progress Dashboard ← Flask API ← Database
     ↓
Retro Website ← JSON API ← Database
```

### Tech Stack

**Backend**:
- Python 3.x
- SQLite database with automatic migrations
- YouTube Data API v3
- Google Gemini API (vision analysis)
- Ollama (local LLM for transcripts)
- Flask (REST APIs)

**Frontend**:
- Pure HTML/CSS/JavaScript (no frameworks)
- 2005-era retro design aesthetics
- Responsive layouts with authentic mid-2000s styling

**AI Models**:
- Gemini 2.0 Flash (primary - visual analysis)
- Gemini 1.5 Flash (fallback)
- Llama 3.2 (Ollama - transcript analysis)

### Project Structure

```
DingerStats/
├── src/
│   ├── analyzers/           # AI analysis engines
│   │   ├── gemini_analyzer.py          # Gemini visual analysis
│   │   └── ollama_transcript_analyzer.py  # Ollama transcript analysis
│   ├── youtube/
│   │   └── youtube_client.py           # YouTube API wrapper
│   └── scripts/
│       ├── process_videos.py           # Main processing script
│       ├── mark_videos.py              # Manual video filtering
│       └── fetch_playlists.py          # Fetch video metadata
├── database/
│   ├── db_manager.py        # Database operations
│   └── schema.sql           # Database schema
├── webapp/
│   ├── backend/
│   │   ├── api.py           # Main website API
│   │   └── progress_api.py  # Progress dashboard API
│   └── frontend/
│       ├── index.html       # Main website
│       ├── classic-10.html  # Classic 10 tournament page
│       └── progress.html    # Real-time progress dashboard
└── docs/                    # Documentation (you are here!)
```

## Key Features

### Current

✅ **Multi-Source Analysis**
- Gemini visual analysis with multiple prompt versions
- Ollama local transcript analysis for validation
- Automatic version tracking and comparison

✅ **Video Filtering**
- Manually mark videos as "not a game" (drafts, analysis, etc.)
- Exclude non-game content from statistics
- `manual_review` flag for user-confirmed classifications

✅ **Real-Time Progress Dashboard**
- Live tracking of analysis progress
- Per-analyzer and per-version statistics
- Success/failure metrics
- Recent activity feed
- Auto-refreshes every 5 seconds

✅ **Retro Website**
- Authentic 2005 web design
- Tournament brackets with sliding door animations
- Player profiles and statistics
- Head-to-head matchup records
- Game summaries with commentary highlights

✅ **Automatic Database Migrations**
- Schema changes applied automatically
- Safe handling of existing data
- No manual SQL required

### Future Roadmap

**Phase 1: Enhanced Validation** (Next)
- Side-by-side comparison UI for Gemini vs Ollama results
- Confidence scoring based on multi-source agreement
- Automatic flagging of discrepancies

**Phase 2: Historical Tracking**
- Track accuracy over time per analyzer
- A/B test prompt versions automatically
- Historical performance metrics

**Phase 3: Enhanced UI**
- Advanced statistics (winning streaks, character win rates)
- Video embedding with timestamp links
- Interactive bracket navigation

**Phase 4: Community Features**
- User predictions and brackets
- Comment system on games
- Player profile pages with highlights

## Data Model

### Core Tables

**videos** - YouTube video metadata
- `video_id` (unique)
- `title`, `description`, `published_at`
- `playlist_id` (Classic 10 or Season 10)
- `is_game` (1 = game, 0 = draft/analysis/etc.)
- `manual_review` (1 = user confirmed, 0 = AI guess)

**game_results** - Extracted game data
- `video_id` (foreign key)
- `player_a`, `player_b` (human player names)
- `team_a`, `team_b` (Mario character teams)
- `score_a`, `score_b`, `winner`
- `game_type` (e.g., "Classic 10 - Round 2 - Elimination")
- `game_summary`, `commentary_summary`
- `analyzer_type` (gemini_visual / ollama_transcript)
- `prompt_version` (v1, v2, v3...)
- `confidence` (high / medium / low)
- `model_name` (specific model used)

**processing_log** - Track processing status
- `video_id`
- `status` (pending / processing / completed / failed)
- `error_message`
- `attempt_count`, `last_attempt`

## Development Workflow

### Typical Session

1. **Fetch New Videos**
   ```bash
   python src/scripts/fetch_playlists.py
   ```

2. **Review Videos** (Optional)
   ```bash
   python src/scripts/mark_videos.py --list classic10
   python src/scripts/mark_videos.py --not-game <video_id>
   ```

3. **Analyze Videos**
   ```bash
   # Gemini analysis
   python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2

   # Ollama validation (parallel)
   python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2
   ```

4. **Monitor Progress**
   ```bash
   # Start progress dashboard
   cd webapp/backend && python progress_api.py
   # Open http://localhost:5001
   ```

5. **View Results**
   ```bash
   # Start website
   cd webapp/backend && python api.py
   # Open http://localhost:5000
   ```

## Tournament Formats

### Classic 10 (YERR OUT! Format)

A unique tournament structure with alternating phases:

**Round Structure**:
- Multiple Round-Robin games → Single Elimination game
- Loser of elimination is "YERR OUT!"
- Repeat until Finals

**Game Types**:
- `Classic 10 - Round 1 - Round Robin`
- `Classic 10 - Round 1 - Elimination`
- `Classic 10 - Round 2 - Round Robin`
- `Classic 10 - Round 2 - Elimination`
- `Classic 10 - Finals`

### Season 10 (Traditional Format)

Standard tournament progression:
- `Season 10 - Regular Season`
- `Season 10 - Playoffs`
- `Season 10 - Finals`

## Configuration

### Required Environment Variables

Create a `.env` file:

```env
# YouTube API (for fetching video metadata)
YOUTUBE_API_KEY=your_youtube_api_key

# Google Gemini API (for visual analysis)
GEMINI_API_KEY=your_gemini_api_key

# Playlist IDs
CLASSIC10_PLAYLIST_ID=PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF
SEASON10_PLAYLIST_ID=PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2
```

### Optional: Ollama Setup

For local transcript analysis:

1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama3.2:1b`
3. Ollama runs on `http://localhost:11434` by default

## Stats & Metrics

As of latest analysis:
- **43 Classic 10 videos** tracked
- **~26 games analyzed** with Gemini v2 (60% complete)
- **~17 games analyzed** with Gemini v1 baseline
- **3 games validated** with Ollama v1
- **95%+ Gemini accuracy** on game data extraction

## Contributing

This is a personal project, but the methodology can be adapted for other sports/gaming content analysis projects.

## Credits

Built by Joey Musselman to automatically track Mario Baseball tournament statistics from the Dinger League YouTube channel.

Inspired by traditional sports statistics websites but with authentic 2005-era web design aesthetics.
