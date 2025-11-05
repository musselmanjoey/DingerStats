# DingerStats - Quick Start Guide

## 🚀 Get Running in 10 Minutes

### Prerequisites

- Python 3.8+
- Google Gemini API key (free tier works!)
- YouTube Data API key (free with Google account)
- (Optional) Ollama installed for transcript validation

### Step 1: Clone and Setup Environment (2 min)

```bash
cd C:/Users/musse/Projects/DingerStats

# Create .env file
```

Create `.env` in the project root:

```env
# Required
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Playlist IDs (already configured)
CLASSIC10_PLAYLIST_ID=PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF
SEASON10_PLAYLIST_ID=PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2
```

**Get API Keys**:
- **YouTube API**: https://console.cloud.google.com/ → Enable "YouTube Data API v3" → Create credentials
- **Gemini API**: https://makersuite.google.com/app/apikey → Create API key

### Step 2: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist, install manually:

```bash
pip install google-generativeai google-api-python-client python-dotenv flask flask-cors youtube-transcript-api requests
```

### Step 3: Fetch Video Metadata (2 min)

```bash
python src/scripts/fetch_playlists.py
```

This fetches all video metadata from YouTube and stores it in the database.

**Output**: `✓ Inserted/updated 43 videos`

### Step 4: Analyze Videos with AI (3 min to start, runs in background)

```bash
# Start Gemini visual analysis (recommended - most accurate)
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2
```

This runs in the foreground. Open a new terminal to continue.

**What it does**: Downloads video frames, analyzes with Gemini AI, extracts game data, saves to database.

**Time**: ~30 seconds per video (so ~22 minutes for 43 videos)

### Step 5: Monitor Progress (1 min)

In a new terminal:

```bash
cd webapp/backend
python progress_api.py
```

Open browser: **http://localhost:5001**

You'll see:
- Real-time progress bars
- Success/failure counts
- Recent analyzed games
- Auto-refreshes every 5 seconds

### Step 6: View the Website (1 min)

In another terminal:

```bash
cd webapp/backend
python api.py
```

Open browser: **http://localhost:5000**

Explore:
- **Home Page** - Tournament overview
- **Classic 10** - Tournament bracket with sliding door animations
- **Player Pages** - Stats and head-to-head records (when enough data)

---

## Quick Commands Reference

| Task | Command |
|------|---------|
| **Fetch videos** | `python src/scripts/fetch_playlists.py` |
| **Analyze (Gemini)** | `python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2` |
| **Analyze (Ollama)** | `python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2` |
| **Mark non-game** | `python src/scripts/mark_videos.py --not-game <video_id>` |
| **List videos** | `python src/scripts/mark_videos.py --list classic10` |
| **Progress dashboard** | `cd webapp/backend && python progress_api.py` (port 5001) |
| **Main website** | `cd webapp/backend && python api.py` (port 5000) |

---

## What If I Get Errors?

### "ModuleNotFoundError"
**Problem**: Missing Python packages
**Solution**:
```bash
pip install google-generativeai google-api-python-client python-dotenv flask flask-cors
```

### "API key not found"
**Problem**: `.env` file not configured or in wrong location
**Solution**:
- Ensure `.env` is in project root (`C:/Users/musse/Projects/DingerStats/`)
- Check file has no `.txt` extension (Windows sometimes hides this)
- Verify API keys are valid

### "No videos found"
**Problem**: Playlist IDs incorrect or YouTube API key invalid
**Solution**:
- Verify API key at https://console.cloud.google.com/
- Check playlist IDs in `.env` match the ones above
- Run `python src/scripts/fetch_playlists.py` again

### "Ollama connection refused"
**Problem**: Ollama not installed or not running
**Solution**:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2:1b
ollama serve
```

### "Port already in use"
**Problem**: Another Flask app running on the same port
**Solution**:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or just use a different port by editing the .py file
```

---

## Next Steps

Once you have some games analyzed:

1. **Read ANALYZER_GUIDE.md** - Learn about multi-source validation
2. **Read PROGRESS_DASHBOARD_GUIDE.md** - Understand the metrics
3. **Read DATABASE_SCHEMA.md** - Explore the data model
4. **Check PROJECT_SUMMARY.md** - Understand the architecture

---

## Pro Tips

### Run Multiple Analyzers in Parallel

Validate results by running both Gemini and Ollama:

```bash
# Terminal 1: Gemini analysis
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2

# Terminal 2: Ollama validation (once Ollama is set up)
python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2

# Terminal 3: Progress dashboard
cd webapp/backend && python progress_api.py

# Terminal 4: Main website
cd webapp/backend && python api.py
```

### Filter Out Non-Games

Some videos are drafts, analysis, or other non-game content:

```bash
# List all videos
python src/scripts/mark_videos.py --list classic10

# Mark a video as "not a game"
python src/scripts/mark_videos.py --not-game DvVBLhsfaBs

# Mark multiple
python src/scripts/mark_videos.py --not-game DvVBLhsfaBs abc123 xyz789
```

This excludes them from statistics and analysis.

### Try Different Prompt Versions

Test improvements to prompts:

```bash
# v1 = original prompt
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v1

# v2 = improved game type detection
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2
```

The progress dashboard shows results per version so you can compare accuracy.

---

## Typical Workflow

```bash
# 1. Morning: Fetch any new videos
python src/scripts/fetch_playlists.py

# 2. Review and filter non-games
python src/scripts/mark_videos.py --list classic10
python src/scripts/mark_videos.py --not-game <any_draft_videos>

# 3. Start analysis (runs in background)
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2

# 4. Monitor progress while working on other stuff
cd webapp/backend && python progress_api.py
# Open http://localhost:5001

# 5. View results when done
cd webapp/backend && python api.py
# Open http://localhost:5000
```

---

## Success Indicators

You're ready to go when you see:

✅ Database created: `database/dingerstats.db`
✅ Videos fetched: 40+ videos in database
✅ First game analyzed: Progress dashboard shows activity
✅ Website loads: Homepage displays tournament info
✅ Bracket renders: Classic 10 page shows tournament structure

---

## Need Help?

- **Read the docs**: PROJECT_SUMMARY.md has detailed architecture info
- **Check the logs**: The processing scripts print detailed progress
- **Inspect the database**: Use any SQLite browser to explore `database/dingerstats.db`
- **Look at examples**: The `webapp/frontend/` folder has working HTML/CSS examples

Happy stat tracking! 📊⚾
