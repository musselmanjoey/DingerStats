# Mario Baseball Stats Tracking Project - Claude Code Briefing

## Project Overview
We're building an automated system to analyze Mario Superstar Baseball gameplay videos from the YouTube channel "Dinger City" and extract detailed baseball statistics. The goal is to track every pitch, at-bat, and game statistic across their entire video library using AI/ML techniques.

## Project Background
- **Channel**: Dinger City (Mario Superstar Baseball content)
- **Upload Schedule**: Daily uploads 
- **Content**: Competitive Mario Baseball gameplay
- **Scope**: Track all baseball statistics a real team would measure
- **Timeline**: Start with new uploads, eventually process entire archive

## Technical Approach - Human-Centered Design Philosophy
We're following a human-centered approach that mimics how humans naturally track baseball:
- **Audio analysis** for complex, fast events (pitch calls, inning transitions)
- **Visual analysis** for obvious information (scores, player identification)
- This approach is more robust than trying to force computer vision to do everything

## Development Phases

### Phase 1: Audio Processing (START HERE)
**Goal**: Build the foundation using audio cues for game structure

**Key Components**:
1. **Video/Audio Download**: Use `yt-dlp` to extract audio from YouTube videos
2. **Inning Detection**: Use `librosa` to detect specific sound that plays at start/end of innings
3. **Audio Pattern Matching**: Use `scipy.signal.correlate()` to find sound patterns
4. **Pitch Call Detection**: Use speech recognition for announcer calls ("strike", "ball", etc.)

**Libraries to Use**:
- `yt-dlp` - YouTube video downloading
- `librosa` - Audio analysis and processing
- `scipy` - Signal processing and correlation
- `speech_recognition` - For announcer call detection

### Phase 2: Database Design
**Goal**: Structure data storage for comprehensive baseball statistics

**Core Tables**:
```sql
games: game_id, date, home_team, away_team, final_home_score, final_away_score
players: player_id, player_name, team
innings: inning_id, game_id, inning_number, start_timestamp, end_timestamp
at_bats: at_bat_id, game_id, inning_id, player_id, final_result
pitches: pitch_id, at_bat_id, pitch_number, result, audio_timestamp
```

### Phase 3: Video Processing (Future)
**Goal**: Extract visual statistics and player information

**Components**:
- Frame extraction from videos using OpenCV
- Template matching for UI elements (scores, player highlights)
- OCR with Tesseract for reading game text
- Player identification when highlighted as current batter

**UI Considerations**:
- Each season has consistent UI within itself
- ~30 different UI versions across all seasons
- May need season-specific templates or version detection

## Coding Standards and Practices

### Keep It Simple
- **Start small**: Build one component at a time and test thoroughly
- **Readable code**: Use clear variable names and add comments explaining baseball logic
- **Modular design**: Each function should do one thing well
- **Error handling**: Account for edge cases (corrupted audio, missing files, etc.)

### Code Organization
```
project_structure/
├── audio_processing/
│   ├── download.py
│   ├── inning_detection.py
│   └── pitch_recognition.py
├── database/
│   ├── models.py
│   └── setup.py
├── video_processing/  # Future phase
├── config/
└── main.py
```

### Development Best Practices
1. **Test with small samples first**: Use 1-2 short videos before processing entire archives
2. **Incremental development**: Get basic functionality working before adding complexity  
3. **Storage management**: Process one video at a time, clean up temp files to avoid storage issues
4. **Configuration-driven**: Use config files for things like audio thresholds, UI coordinates
5. **Logging**: Track what's working and what's failing for debugging

## Communication and Learning Guidelines

### Explanation Standards
- **Explain every concept**: Don't assume familiarity with audio processing, ML, or baseball terminology
- **Show examples**: Provide concrete examples of what each function does
- **Step-by-step breakdowns**: Walk through complex logic line by line
- **Check understanding**: If something seems unclear, repeat explanation in simpler terms

### Code Review Process
- **Comment thoroughly**: Explain what each section does in plain English
- **Show expected inputs/outputs**: Demonstrate what data looks like at each stage
- **Explain library choices**: Why we're using librosa vs. other options
- **Debug together**: If something doesn't work, walk through troubleshooting steps

## Immediate Next Steps

1. **Environment Setup**: Install required libraries (`yt-dlp`, `librosa`, `scipy`)
2. **Basic Audio Download**: Create script to download audio from a single Dinger City video
3. **Audio Loading**: Use librosa to load and examine audio data structure
4. **Manual Sound Identification**: Find the inning transition sound in audio and crop it as reference
5. **Pattern Matching**: Implement basic correlation to find all instances of that sound

## Success Metrics
- **Phase 1 Success**: Can reliably detect inning transitions from audio
- **Database Success**: Can store and query game/inning/pitch data efficiently  
- **Overall Success**: Can process any Dinger City video and output comprehensive baseball statistics

## Project Philosophy
This is an ambitious but achievable project that combines web scraping, audio processing, computer vision, and database design. The key is building incrementally and testing each component thoroughly. The human-centered approach (audio for complex events, visual for obvious information) should make this more reliable than pure computer vision approaches.

Start simple, test frequently, and build up complexity gradually. The end goal is a system that can automatically analyze any Mario Baseball video and produce detailed statistics comparable to what a human scorekeeper would track.