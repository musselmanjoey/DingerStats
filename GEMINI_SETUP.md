# Gemini YouTube Analysis Setup Guide

This guide will help you set up the YouTube video analysis pipeline using Gemini API.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

#### YouTube Data API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy your API key

#### Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API Key**
4. Copy your API key

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your keys
YOUTUBE_API_KEY=your_youtube_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 4. Run the Pipeline

#### Fetch videos from a playlist
```bash
# Fetch all videos from a playlist
python process_dinger_videos.py fetch --playlist PLAYLIST_ID_HERE

# Fetch with title filters (only videos matching these patterns)
python process_dinger_videos.py fetch --playlist PLAYLIST_ID_HERE --filter "Mario Baseball" "Super Sluggers"

# Exclude certain videos
python process_dinger_videos.py fetch --playlist PLAYLIST_ID_HERE --exclude "Trailer" "Announcement"

# Limit number of videos
python process_dinger_videos.py fetch --playlist PLAYLIST_ID_HERE --max 50
```

#### Analyze videos with Gemini
```bash
# Analyze all unprocessed videos
python process_dinger_videos.py analyze

# Analyze with custom rate limit (default is 6 seconds between requests)
python process_dinger_videos.py analyze --delay 10

# Analyze only first 10 videos
python process_dinger_videos.py analyze --max 10
```

#### View statistics
```bash
python process_dinger_videos.py stats
```

#### View results
```bash
# Show 10 most recent results
python process_dinger_videos.py results

# Show 50 most recent results
python process_dinger_videos.py results --limit 50
```

## Finding Playlist IDs

### Method 1: From Playlist URL
The playlist ID is in the URL after `list=`:
```
https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxxxxx
                                      ^^^^^^^^ This is the playlist ID
```

### Method 2: Using the YouTube Fetcher
```bash
# Run the interactive fetcher
python youtube_fetcher.py

# It will prompt for channel URL and show all playlists
```

## Rate Limits & Costs

### YouTube Data API (Free Tier)
- **Quota**: 10,000 units per day
- **Cost per playlist fetch**: ~3-5 units
- **Cost per video details**: 1 unit per 50 videos
- You can process thousands of videos per day for free

### Gemini API

#### Free Tier
- **Rate limit**: 10 requests/minute
- **Daily limit**: 250 requests/day
- **Video processing**: 8 hours total video time per day
- With 6-second delays, you can process **~250 videos/day for FREE**

#### Paid Tier (Pay-as-you-go)
- **Rate limit**: 2,000 requests/minute
- **No daily limits**
- **Cost**: $0.30-0.80 per video (10-minute videos)
- **100 videos**: ~$1.50-2.00
- **1,000 videos**: ~$15-25

## Example Workflow

### Complete pipeline for Dinger City videos:

```bash
# 1. Fetch Mario Baseball game videos
python process_dinger_videos.py fetch \
  --playlist PLxxxxxxxxxxxxxx \
  --filter "Mario.*Baseball" "Super.*Sluggers" \
  --exclude "Compilation" "Highlights" "Trailer"

# 2. Check what was fetched
python process_dinger_videos.py stats

# 3. Analyze the videos (free tier: ~40 videos per day with delays)
python process_dinger_videos.py analyze --max 40

# 4. View results
python process_dinger_videos.py results --limit 20
```

## Database

Videos and results are stored in `database/dingerstats.db` (SQLite).

### Tables:
- **videos**: Video metadata (title, duration, URL, etc.)
- **game_results**: Parsed game results (teams, scores, winners)
- **processing_log**: Processing status and errors

### Accessing the database directly:
```bash
# Using sqlite3 command-line
sqlite3 database/dingerstats.db

# View all videos
SELECT video_id, title FROM videos;

# View all results
SELECT v.title, gr.team_a, gr.team_b, gr.score_a, gr.score_b, gr.winner
FROM game_results gr
JOIN videos v ON gr.video_id = v.video_id;
```

## Troubleshooting

### "No module named 'google'"
```bash
pip install google-genai google-api-python-client
```

### "API key not set"
Make sure you created a `.env` file with both API keys.

### "Rate limit exceeded"
- **YouTube**: You've hit the daily quota (10,000 units). Wait until tomorrow or enable billing.
- **Gemini Free Tier**: 250 requests/day limit. Wait or upgrade to paid tier.
- **Gemini Paid Tier**: Increase delay between requests.

### "Video analysis failed"
- Video might be private/unlisted (Gemini only works with public videos)
- Video might be too long (max 3 hours)
- Network error - check your internet connection

### "Unable to parse result"
The Gemini response couldn't be parsed. Check `raw_response` in the database to see what Gemini returned. You may need to adjust the prompt or parsing logic.

## Testing Individual Components

### Test YouTube fetcher:
```bash
python youtube_fetcher.py
```

### Test Gemini analyzer:
```bash
python gemini_analyzer.py
```

Both scripts have interactive test modes.

## Next Steps

1. **Start with a small test**: Fetch and analyze 5-10 videos first
2. **Check accuracy**: Review results to ensure Gemini is correctly identifying teams/scores
3. **Scale up**: Once confident, process larger batches
4. **Adjust filters**: Refine your title filters to get exactly the videos you want
5. **Export data**: Query the SQLite database for analysis, reports, or dashboards

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Project Research Summary](gemini-youtube-research-summary.md)
