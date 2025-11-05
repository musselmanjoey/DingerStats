# Progress Dashboard Guide

## Overview

The Progress Dashboard provides real-time monitoring of video analysis progress across multiple analyzers and prompt versions.

**URL**: http://localhost:5001

**Auto-refresh**: Every 5 seconds

## Starting the Dashboard

```bash
cd webapp/backend
python progress_api.py
```

Open browser to **http://localhost:5001**

## Dashboard Features

### 1. Statistics Cards

Each card represents one analyzer/version combination:

**Card Header**:
- Playlist name (Classic 10 / Season 10)
- Analyzer badge (Gemini Visual / Ollama Transcript)
- Version (v1, v2, etc.)

**Progress Bar**:
- Visual representation of completion %
- Shows percentage analyzed out of total videos

**Statistics Grid**:
- **Analyzed**: Total videos processed
- **Success**: Games with extracted data (green)
- **Failed**: Videos where analysis failed (red)
- **Remaining**: Videos not yet analyzed (orange)

### 2. Recent Activity Feed

Shows the last 10 analyzed videos with:
- Video title
- Analyzer and version used
- Success/failure status
- Player matchup (if successful)
- Timestamp of analysis

**Color coding**:
- Green left border = Success
- Red left border = Failed

### 3. Real-Time Updates

Dashboard refreshes automatically every 5 seconds showing:
- Progress bars updating as videos complete
- New items appearing in activity feed
- Statistics incrementing

Leave it open while analysis runs in another terminal!

## Example Dashboard View

```
┌─────────────────────────────────────┐
│ Classic 10                          │
│ [Gemini Visual v2]                  │
│ ████████████░░░░░░░ 60%             │
│ Analyzed: 26  Success: 23           │
│ Failed: 3     Remaining: 17         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Classic 10                          │
│ [Ollama Transcript v1]              │
│ ██░░░░░░░░░░░░░░░░░░ 7%             │
│ Analyzed: 3   Success: 3            │
│ Failed: 0     Remaining: 40         │
└─────────────────────────────────────┘

Recent Activity:
├─ Tyler vs Hunter (Ollama v1) ✓
├─ Jason vs Andrew (Gemini v2) ✓
├─ Draft Analysis (Gemini v2) ✗
└─ ...
```

## Interpreting the Data

### High Success Rate (>90%)
✅ Analyzer working well
✅ Prompts are effective
✅ Videos have clear data

**Action**: Continue with this analyzer/version

### Moderate Success (70-90%)
⚠️ Some extraction issues
⚠️ May need prompt improvements
⚠️ Check failed videos for patterns

**Action**: Review failures, iterate on prompts

### Low Success (<70%)
❌ Systematic problem
❌ Wrong model or prompt
❌ Poor video/transcript quality

**Action**: Stop, investigate root cause

### All Failures
❌ Configuration error
❌ API issues
❌ Model problems

**Action**: Check logs immediately

## Common Scenarios

### Scenario: Gemini Running, Ollama Not Started

```
Gemini Visual v2:  ████████░░ 40% (17/43)
Ollama Transcript: (No data)
```

**Meaning**: Only Gemini analysis has run. Start Ollama for validation:

```bash
python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2
```

### Scenario: Both Analyzers Running

```
Gemini Visual v2:  ████████████ 60% (26/43)
Ollama Transcript: ██░░░░░░░░░░ 7% (3/43)
```

**Meaning**: Gemini faster, Ollama slower. This is expected.

### Scenario: High Failure Rate

```
Ollama Transcript v2: █████░░░░░░ 23% (10/43)
Success: 2  Failed: 8  Remaining: 33
```

**Meaning**: Ollama v2 having major issues (8/10 failed).

**Action**:
1. Check running terminal for error messages
2. Review ANALYZER_GUIDE.md troubleshooting
3. Consider switching models or versions

## API Endpoints

The dashboard consumes this API:

**GET `/api/progress`**

Returns:
```json
{
  "stats": [
    {
      "playlist": "Classic 10",
      "analyzer": "gemini_visual",
      "version": "v2",
      "total": 43,
      "analyzed": 26,
      "successful": 23,
      "failed": 3,
      "remaining": 17
    },
    ...
  ],
  "recent_activity": [
    {
      "title": "Game Title",
      "analyzer": "gemini_visual",
      "version": "v2",
      "success": true,
      "players": "Tyler vs Hunter",
      "winner": "Tyler",
      "timestamp": "2025-11-05 21:00:42"
    },
    ...
  ]
}
```

## Advanced Usage

### Multiple Terminal Workflow

**Terminal 1**: Gemini Analysis
```bash
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2
```

**Terminal 2**: Ollama Validation
```bash
python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2
```

**Terminal 3**: Progress Dashboard
```bash
cd webapp/backend && python progress_api.py
```

**Browser**: Watch http://localhost:5001 while working

### Testing Prompt Changes

Run v1 and v2 simultaneously to compare:

```bash
# Terminal 1
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v1

# Terminal 2
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2
```

Dashboard shows side-by-side comparison in real-time!

### Monitoring Long-Running Jobs

Start analysis, minimize terminals, leave dashboard open. Check back periodically to see:
- How many videos processed
- Success rate
- Estimated time remaining (total - analyzed)

## Troubleshooting

### "No data" or Empty Dashboard

**Problem**: API not finding database or no analysis run yet

**Solutions**:
1. Check database exists: `ls database/dingerstats.db`
2. Run analysis: `python src/scripts/process_videos.py ...`
3. Verify progress API connected to correct DB (check logs)

### Dashboard Not Updating

**Problem**: Analysis finished but dashboard stuck

**Solutions**:
1. Hard refresh browser (Ctrl+F5)
2. Check analysis script still running
3. Restart progress API

### Wrong Statistics

**Problem**: Numbers don't match what you expect

**Solutions**:
1. Check `is_game` filter - non-games excluded from totals
2. Verify analyzer_type and prompt_version in database
3. Query database directly to confirm:
   ```bash
   sqlite3 database/dingerstats.db
   SELECT analyzer_type, prompt_version, COUNT(*) FROM game_results GROUP BY analyzer_type, prompt_version;
   ```

### Port Already in Use

**Problem**: "Address already in use" error

**Solution**:
```bash
# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F

# Or edit progress_api.py to use different port
```

## Tips

1. **Leave it open**: Dashboard designed to run in background while you work
2. **Multiple monitors**: Put dashboard on secondary monitor during long analysis runs
3. **Compare versions**: Start v1 and v2 simultaneously to A/B test prompts
4. **Activity feed**: Quick way to spot systematic errors (e.g., all failures same player name)
5. **Success rate**: Quick health check - >90% = good, <70% = investigate

## Future Enhancements

**Planned features**:
- Download results as CSV
- Historical trend charts (progress over time)
- Estimated time remaining
- Notifications when analysis completes
- Comparison view (Gemini vs Ollama side-by-side)
- Confidence scoring visualization
