# Multi-Source Analyzer Guide

## Philosophy: Don't Trust, Verify

Single AI models make mistakes. DingerStats uses **multi-source data validation**:

1. **Gemini Visual** analyzes video frames (scoreboard, UI elements)
2. **Ollama Transcript** analyzes YouTube transcripts (commentary, player mentions)
3. **Version Tracking** compares different prompt versions
4. **Manual Review** allows human verification

Cross-validate results to catch errors and improve accuracy over time.

## Analyzer Types

### Gemini Visual (`gemini_visual`)

**What it does**: Downloads video frames and analyzes on-screen information

**Strengths**:
- Sees scoreboard, player names, team compositions
- Detects game type from UI elements
- 95%+ accuracy on score extraction
- Fast (~30 seconds per video)

**Weaknesses**:
- Costs money (API usage)
- Requires internet connection
- Can miss context from commentary

**Best for**: Primary analysis, accurate scores/winners

**Models**:
- `gemini-2.0-flash-exp` (default, most accurate)
- `gemini-1.5-flash` (fallback)

### Ollama Transcript (`ollama_transcript`)

**What it does**: Fetches YouTube transcripts and analyzes with local LLM

**Strengths**:
- Completely free (local model)
- Works offline (after model download)
- Captures commentary context
- Good for validation

**Weaknesses**:
- Slower (minutes per video on weak hardware)
- Less accurate on exact scores
- Requires Ollama installation
- Struggles with brief/noisy transcripts

**Best for**: Validation, detecting game type from commentary

**Models**:
- `llama3.2:1b` (fastest, lower accuracy)
- `llama3.2:3b` (balanced, but slow on weak hardware)

## Prompt Versions

Track different prompt strategies to measure improvements:

### v1 (Baseline)
- Original simple prompt
- Basic game data extraction
- ~85% accuracy on game type

### v2 (Improved Game Type Detection)
- Enhanced tournament format understanding
- Better Round Robin vs Elimination detection
- Explicit YERR OUT format handling
- ~95% accuracy on game type

### v3+ (Future)
- Could add character-specific extraction
- Commentary sentiment analysis
- Confidence scoring improvements

## Usage

### Run Analysis

```bash
# Gemini v2 (recommended)
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2

# Ollama v2 (validation)
python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2

# Run both in parallel (different terminals)
```

### Compare Results

Check the progress dashboard (http://localhost:5001) to see:
- Gemini v1: 17/43 (40%)
- Gemini v2: 26/43 (60%)
- Ollama v1: 3/43 (7%)

Or query the database:

```python
from database.db_manager import DatabaseManager

db = DatabaseManager()

# Get Gemini v2 results
results_gemini = db.get_connection().execute("""
    SELECT * FROM game_results
    WHERE analyzer_type = 'gemini_visual' AND prompt_version = 'v2'
""").fetchall()

# Get Ollama v1 results for same video
results_ollama = db.get_connection().execute("""
    SELECT * FROM game_results
    WHERE video_id = 'WbY_IjNfUsQ' AND analyzer_type = 'ollama_transcript'
""").fetchall()

# Compare player names, scores, winners
```

## Validation Workflow

### Step 1: Run Primary Analysis
```bash
python src/scripts/process_videos.py --playlist classic10 --analyzer gemini --version v2
```

### Step 2: Run Validation
```bash
python src/scripts/process_videos.py --playlist classic10 --analyzer ollama --version v2
```

### Step 3: Review Discrepancies

When Gemini and Ollama disagree:

```sql
SELECT
    v.title,
    g1.player_a AS gemini_player_a,
    g2.player_a AS ollama_player_a,
    g1.winner AS gemini_winner,
    g2.winner AS ollama_winner
FROM videos v
JOIN game_results g1 ON v.video_id = g1.video_id AND g1.analyzer_type = 'gemini_visual'
JOIN game_results g2 ON v.video_id = g2.video_id AND g2.analyzer_type = 'ollama_transcript'
WHERE g1.winner != g2.winner;
```

### Step 4: Manual Verification

Watch the video yourself and confirm the correct data. Update the database:

```python
# If Gemini was correct, no action needed (use it as source of truth)
# If Ollama was correct, note it for prompt improvement

# Or add a confidence boost system:
# UPDATE game_results SET confidence = 'high' WHERE both agree
```

## Tips for Accurate Analysis

### Filter Non-Games First
```bash
python src/scripts/mark_videos.py --list classic10
python src/scripts/mark_videos.py --not-game <draft_video_id>
```

This prevents wasting API calls on draft/analysis videos.

### Use Progress Dashboard
Monitor in real-time to catch systematic errors early:
- All failures on specific player names? → Prompt issue
- Low confidence across the board? → Transcript quality issue

### Test on Known Games
Before processing all 43 videos, test on 2-3 games you've watched:

```bash
# Process just one video
python -c "
from src.analyzers.gemini_analyzer import GeminiAnalyzer
analyzer = GeminiAnalyzer(prompt_version='v2')
result, raw = analyzer.analyze_game_video('WbY_IjNfUsQ')
print(result)
"
```

Verify it extracted correct data before batch processing.

## Model Selection

### Gemini

Always use latest flash model for best accuracy:
- `gemini-2.0-flash-exp` (current best)
- Falls back to `gemini-1.5-flash` if needed

Configure in `src/analyzers/gemini_analyzer.py`.

### Ollama

Choose based on your hardware:

| Model | Size | Speed (per video) | Accuracy | Use Case |
|-------|------|-------------------|----------|----------|
| `llama3.2:1b` | 1.3GB | ~1-2 min | 60% | Fast validation, weak hardware |
| `llama3.2:3b` | 2GB | ~5+ min | 75% | Better accuracy, timeout risk |

Configure in `src/analyzers/ollama_transcript_analyzer.py`.

**Current default**: `llama3.2:1b` (speed > accuracy for validation)

## Database Schema

All results stored with analyzer tracking:

```sql
CREATE TABLE game_results (
    id INTEGER PRIMARY KEY,
    video_id TEXT,
    player_a TEXT,
    player_b TEXT,
    score_a INTEGER,
    score_b INTEGER,
    winner TEXT,
    game_type TEXT,
    analyzer_type TEXT,  -- 'gemini_visual' or 'ollama_transcript'
    prompt_version TEXT, -- 'v1', 'v2', etc.
    model_name TEXT,     -- specific model used
    confidence TEXT,     -- 'high', 'medium', 'low'
    analyzed_at TIMESTAMP
);
```

This enables:
- Compare same video analyzed by different methods
- Track which prompt version performed best
- A/B test model changes
- Historical accuracy tracking

## Future Enhancements

**Phase 1: Comparison UI**
- Side-by-side Gemini vs Ollama results
- Highlight discrepancies
- Manual confirmation workflow

**Phase 2: Automatic Confidence Scoring**
```python
if gemini_result == ollama_result:
    confidence = 'high'
elif similar(gemini_result, ollama_result, threshold=0.8):
    confidence = 'medium'
else:
    confidence = 'low'  # manual review needed
```

**Phase 3: Active Learning**
- Learn from manual corrections
- Improve prompts based on errors
- Model fine-tuning (if feasible)

## Troubleshooting

**Gemini: "Rate limit exceeded"**
- Wait and retry (free tier has limits)
- Upgrade to paid tier
- Add delays between requests

**Ollama: "Timeout after 300 seconds"**
- Use faster model (`llama3.2:1b`)
- Reduce transcript length (increase truncation)
- Increase timeout in `ollama_transcript_analyzer.py`

**Ollama: "Invalid JSON response"**
- Smaller models struggle with JSON formatting
- Consider using `llama3.2:3b` despite timeout risk
- Improve JSON extraction in `parse_response()`

**Both: Wrong game type**
- Review prompt in analyzer file
- Check transcript quality (YouTube auto-generated can be poor)
- Manually verify video has clear game type indicators
