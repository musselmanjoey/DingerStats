# DingerStats Project Structure

## Directory Layout

```
DingerStats/
├── src/                    # Main source code
│   ├── analyzers/          # Video analysis tools
│   │   ├── gemini_analyzer.py      # Gemini API video analyzer
│   │   └── youtube_fetcher.py      # YouTube data fetching
│   ├── utils/              # Utility modules
│   │   ├── player_normalizer.py    # Player name normalization
│   │   └── game_type_normalizer.py # Game type normalization
│   └── scripts/            # Processing scripts
│       ├── process_dinger_videos.py    # Main video processing
│       ├── reprocess_classic10_v2.py   # v2 prompt reprocessing
│       ├── compare_prompt_versions.py  # v1 vs v2 comparison
│       └── fetch_classics_and_seasons.py # Fetch playlist data
│
├── database/               # Database and schema
│   ├── db_manager.py       # Database operations
│   └── dingerstats.db      # SQLite database
│
├── webapp/                 # Static website
│   ├── frontend/           # HTML/CSS/JS
│   │   ├── index.html                  # Main stats page
│   │   ├── index_template_2005.html    # 2005 retro template
│   │   ├── classic_10_template_2005.html  # Classic 10 YERR OUT! template
│   │   └── season_template_2005.html   # Season tournament template
│   ├── backend/            # Stats calculation
│   │   └── stats_calculator.py
│   ├── generate_static_site.py         # Build main site
│   └── generate_tournament_pages.py    # Build tournament pages
│
├── tools/                  # Development tools
│   └── debug/
│       └── debug_ui.py     # Interactive database inspector
│
├── archive/                # Old code (for reference)
│   ├── old_audio_detection/    # Original audio-based inning detection
│   └── old_docs/               # Old project documentation
│
└── docs/                   # Documentation
    ├── README.md
    ├── GEMINI_SETUP.md
    ├── PROMPT_VERSIONING.md
    └── SEASON10_OVERNIGHT_GUIDE.md
```

## Quick Start

### 1. Process Videos
```bash
# Process new videos from a playlist
python src/scripts/process_dinger_videos.py analyze --playlist PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF

# Process with specific prompt version
python src/scripts/process_dinger_videos.py analyze --playlist <ID> --prompt-version v2
```

### 2. Generate Website
```bash
# Generate static site with latest stats
cd webapp
python generate_static_site.py
```

### 3. Debug/Inspect Data
```bash
# Interactive UI to explore database
python tools/debug/debug_ui.py

# Compare prompt versions
python src/scripts/compare_prompt_versions.py
```

## Key Concepts

### Prompt Versioning
- **v1**: Original prompt (generic game type detection)
- **v2**: Improved prompt (explicit YERR OUT! format instructions)
- All games tagged with `prompt_version` for A/B testing

### Normalization Layers
- **Player Normalizer**: Maps AI name variations to canonical names
- **Game Type Normalizer**: Maps inconsistent game types to structured format

### Tournament Formats
- **Classic 10 (YERR OUT!)**: Round-Robin → Elimination → Repeat until Finals
- **Season**: Traditional Regular Season → Playoffs → Finals

## Development Workflow

1. **Add videos**: Use `fetch_classics_and_seasons.py` to add playlists
2. **Process**: Run `process_dinger_videos.py` to analyze videos
3. **Inspect**: Use `debug_ui.py` to verify data quality
4. **Generate**: Run `generate_static_site.py` to build website
5. **Deploy**: Push to Vercel

## Database Schema

See `database/db_manager.py` for full schema. Key tables:
- `videos`: YouTube video metadata
- `game_results`: Analyzed game data (with `prompt_version`)
- `processing_log`: Analysis attempt tracking
