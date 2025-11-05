# Prompt Versioning System

## Overview

Implemented a versioning system for Gemini API prompts to allow A/B testing of data quality improvements.

## What Was Changed

### 1. Database Schema
- Added `prompt_version` column to `game_results` table
- All existing 39 records labeled as 'v1'
- New records will default to 'v2'

### 2. Gemini Analyzer (`gemini_analyzer.py`)
- Added `prompt_version` parameter to `analyze_game_video()` method
- Created two prompt methods:
  - `_get_v1_prompt()` - Original prompt with basic game type detection
  - `_get_v2_prompt()` - Improved prompt with explicit Classic 10 YERR OUT! structure

### 3. V2 Prompt Improvements
The v2 prompt provides:
- Detailed explanation of Classic 10's YERR OUT! format
- Clear distinction between round-robin games and elimination games
- Specific game type labels:
  - "Classic 10 - Round 1 - Round Robin"
  - "Classic 10 - Round 1 - Elimination"
  - (etc. for all rounds)
- Instructions to look for video title and commentary indicators

### 4. Game Type Normalizer (`game_type_normalizer.py`)
- Updated to handle both v1 and v2 game type formats
- Maps v2's detailed labels to canonical round structure

### 5. Database Manager (`database/db_manager.py`)
- Updated `insert_game_result()` to accept and store `prompt_version`
- Defaults to 'v2' for new records

## Usage

### Re-process Classic 10 with v2 Prompt
```bash
python reprocess_classic10_v2.py
```
This will:
1. Get all 38 Classic 10 videos
2. Re-analyze them using v2 prompt
3. Store results with prompt_version='v2'
4. Maintain v1 data for comparison

### Compare Results
```bash
python compare_prompt_versions.py
```
This will:
1. Show game type distribution for v1 vs v2
2. Count elimination games in each version
3. Analyze if v2 better matches expected structure

Expected Classic 10 Structure:
- Round 1: ~15 round-robin + 1 elimination (16 total)
- Round 2: ~10 round-robin + 1 elimination (11 total)
- Round 3: ~6 round-robin + 1 elimination (7 total)
- Finals: Championship games
- **Total eliminations: 3-4** (v1 incorrectly detected 16)

## Key Differences: v1 vs v2

### V1 Prompt
- Generic game type question: "Regular Season/Playoff/Elimination/Finals"
- No context about tournament structure
- Result: AI over-labeled games as "elimination" (16 elimination games)

### V2 Prompt
- Explains YERR OUT! format structure
- Distinguishes round-robin from elimination
- Instructs AI to look for specific indicators (video title, commentary)
- Expected result: More accurate elimination detection (~3-4 games)

## Database Queries

### View v1 data:
```sql
SELECT * FROM game_results WHERE prompt_version = 'v1'
```

### View v2 data:
```sql
SELECT * FROM game_results WHERE prompt_version = 'v2'
```

### Compare elimination counts:
```sql
SELECT
    prompt_version,
    COUNT(*) as total_games,
    SUM(CASE WHEN game_type LIKE '%elimination%' THEN 1 ELSE 0 END) as elimination_games
FROM game_results
GROUP BY prompt_version
```

## Next Steps

1. Run `reprocess_classic10_v2.py` to generate v2 data
2. Run `compare_prompt_versions.py` to evaluate results
3. If v2 is better: use v2 prompt for all future processing
4. If v1 is better: refine v2 prompt and repeat

## Cost Considerations

- Re-processing 38 videos = 38 Gemini API requests
- Rate limit: 15 requests/minute (script uses 6 second delay = 10/min)
- Total time: ~4 minutes
- Cost: Free tier (1,500 requests/day)
