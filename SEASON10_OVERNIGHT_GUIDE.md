# Season 10 Overnight Processing Guide

## How to Run

Start the overnight processing:
```bash
python process_season10.py
```

The script will:
- Process all 59 Season 10 videos
- ~6 minutes total runtime (6 seconds per video)
- Save progress after each video
- Create log files for tracking

## How to Track Progress

### Option 1: Check Progress File (Easiest)
```bash
# On Windows
type season10_progress.txt

# View anytime to see current status
```

This shows:
```
Season 10 Processing Progress
Last updated: 2025-11-04 18:30:15

Processed: 25/59 (42.4%)
Successful: 24
Failed: 1
Success rate: 96.0%
```

### Option 2: Check Log File
```bash
# See full log with timestamps
type season10_progress.log

# See just the last 10 lines
powershell -command "Get-Content season10_progress.log -Tail 10"
```

### Option 3: Check Database
```bash
python process_dinger_videos.py stats
```

## While It's Running

The script prints status to console:
```
[2025-11-04 18:25:30] [1/59] Processing: WORLD SERIES PLAYERS Q+A!!...
[2025-11-04 18:25:45]   SUCCESS: Nick vs Dennis - Winner: Nick [Playoff]
[2025-11-04 18:25:51] [2/59] Processing: Is Bowser ACTUALLY the best...
```

## After It's Done

View all results:
```bash
python process_dinger_videos.py results --limit 59
```

Query the database:
```bash
# Show all playoff games
sqlite3 database/dingerstats.db "SELECT player_a, player_b, winner, game_type FROM game_results WHERE game_type LIKE '%Playoff%'"

# Show all elimination games
sqlite3 database/dingerstats.db "SELECT player_a, player_b, winner FROM game_results WHERE game_type LIKE '%Elimination%'"

# Search for walk-off homeruns
sqlite3 database/dingerstats.db "SELECT player_a, player_b, game_summary FROM game_results WHERE game_summary LIKE '%walk-off%'"

# Search for commentary bits
sqlite3 database/dingerstats.db "SELECT player_a, player_b, commentary_summary FROM game_results WHERE commentary_summary IS NOT NULL"
```

## If Something Goes Wrong

The script has built-in error handling:
- Failed videos are logged
- Processing status is saved
- You can restart and it will skip already-processed videos

To restart:
```bash
python process_season10.py
```

It will automatically skip videos already in the database.

## Cost & Time

**On Free Tier:**
- 59 videos = 59 API requests
- Well within 250/day limit ✓
- Total time: ~6 minutes
- Cost: FREE (within free tier)

**Data Stored:**
For each video you get:
- Player names
- Team names
- Scores
- Winner
- Game type (Regular/Playoff/Elimination/Finals)
- Game highlights summary
- Commentary highlights
- Full Gemini response

All queryable forever, no additional API costs!
