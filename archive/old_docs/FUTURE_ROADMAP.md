# DingerStats: Future Development Roadmap

## Project Vision
Build a comprehensive automated system for analyzing Mario Superstar Baseball gameplay videos, extracting detailed statistics, and providing insights into team performance and game outcomes.

## Development Priorities

### Phase 1: User Interface & Sample Collection 🎯 **PRIORITY**
**Goal**: Create a simple UI to streamline audio sample collection and potentially crowdsource improvements.

#### 1.1 Build Simple UI for Easier Clip Collection
- **Description**: Replace manual Audacity workflow with user-friendly interface
- **Features**:
  - Video URL input field
  - Audio player with waveform visualization
  - Click-to-select time ranges for sample extraction
  - Export selected clips as training samples
  - Batch processing for multiple time ranges
- **Technology Stack**: 
  - Frontend: Streamlit or Flask web interface
  - Backend: Existing Python audio processing pipeline
  - Visualization: matplotlib/plotly for waveforms
- **Potential Public Feedback Integration**:
  - Community-driven sample collection
  - Crowdsourced validation of detected transitions
  - User ratings for sample quality
- **Deliverables**:
  - Web-based sample extraction tool
  - User guide for sample collection
  - Sample validation interface

### Phase 2: Audio Event Detection Expansion 🔊
**Goal**: Implement detection for all major game audio events to create comprehensive game state tracking.

#### 2.1 Implement "Out" Audio Detection
- **Description**: Detect Lakitu's "Out!" calls to validate inning transitions (3 outs = half-inning end)
- **Approach**:
  - Extract "out" samples from gameplay footage
  - Multi-template detection similar to chime system
  - Cross-validation with inning chimes for higher accuracy
- **Expected Impact**: Push inning detection from 71.4% → 90%+ accuracy
- **Technical Requirements**:
  - Sample collection from various game contexts
  - Filtering to separate from commentary
  - Sequential counting logic (detect 3 consecutive outs)

#### 2.2 Implement Hit Audio Detection  
- **Description**: Detect various hit types (single, double, triple, home run) through bat-ball contact sounds
- **Audio Cues to Detect**:
  - Bat crack sound patterns
  - Lakitu's hit announcements ("It's a hit!", "Home run!")
  - Crowd reaction patterns
- **Challenges**:
  - Multiple hit sound variations
  - Distinguishing hit types by audio characteristics
  - Separating successful hits from foul balls

#### 2.3 Implement Walk Audio Detection
- **Description**: Detect walks, strikeouts, and other at-bat outcomes
- **Audio Cues to Detect**:
  - Lakitu's "Ball four, take your base!" 
  - "Strike three, you're out!"
  - Various pitch call announcements
- **Integration**: Combine with hit detection for complete at-bat outcome tracking

### Phase 3: Database System 💾
**Goal**: Implement persistent storage for game statistics and historical analysis.

#### 3.1 Implement Basic Database Reads and Writes
- **Description**: Store detected events and game statistics in structured database
- **Schema Design**:
  - Games table (video_id, date, teams, final_score)
  - Innings table (game_id, inning_number, half, events)
  - AtBats table (game_id, inning_id, batter, outcome, timestamp)
  - Events table (game_id, timestamp, event_type, confidence)
- **Technology**: 
  - SQLite for development/testing
  - PostgreSQL for production
  - SQLAlchemy ORM for Python integration
- **Features**:
  - Automated event storage from detection pipeline
  - Query interface for statistics retrieval
  - Data validation and integrity checks
  - Export capabilities (CSV, JSON)

### Phase 4: Computer Vision Integration 👁️
**Goal**: Add visual analysis to complement audio detection and extract information not available through audio.

#### 4.1 Implement Video Detection for Score
- **Description**: Read scoreboard display to track runs, balls, strikes, outs
- **Technical Approach**:
  - OCR (Optical Character Recognition) on scoreboard region
  - Template matching for score display elements
  - Frame-by-frame analysis during key moments
- **Challenges**:
  - Scoreboard position varies by camera angle
  - Text clarity issues in compressed video
  - Distinguishing score updates from display artifacts

#### 4.2 Implement Video Detection for At-Bat/Team Captain
- **Description**: Identify batting team, player characters, and lineup information
- **Visual Elements to Detect**:
  - Team captain icons/indicators
  - Character models at bat
  - Team colors and uniforms
  - Batting order displays
- **Applications**:
  - Player performance tracking
  - Team composition analysis
  - Character usage statistics
- **Technical Approach**:
  - Object detection models (YOLO, R-CNN)
  - Character classification using pre-trained models
  - Template matching for UI elements

## Implementation Timeline

### Short Term (1-3 months)
1. **UI for clip collection** - Streamline sample creation workflow
2. **"Out" detection system** - Cross-validate inning transitions
3. **Database foundation** - Basic storage and retrieval

### Medium Term (3-6 months)  
4. **Hit detection system** - Expand event coverage
5. **Walk detection system** - Complete at-bat outcome tracking
6. **Score video detection** - Add visual game state tracking

### Long Term (6+ months)
7. **Player/team video detection** - Character and lineup analysis
8. **Advanced analytics** - Performance metrics and insights
9. **Public interface** - Community-driven improvements and validation

## Technical Considerations

### Scalability Requirements
- **Processing Speed**: Target <5 minutes analysis time for 20-minute video
- **Storage**: Efficient database design for thousands of games
- **Memory**: Optimize for processing multiple videos simultaneously

### Quality Assurance
- **Validation Pipeline**: Automated testing against known ground truth
- **Confidence Scoring**: Reliability metrics for each detection type
- **Manual Review Interface**: Flag uncertain detections for human verification

### Integration Architecture
- **Modular Design**: Each detection system as independent, composable modules
- **Pipeline Orchestration**: Coordinated processing of audio + video analysis
- **Result Aggregation**: Combine multiple detection sources for final game state

## Future Expansion Opportunities

### Community Features
- **Public Dashboard**: Display statistics and insights from analyzed games
- **Crowdsourced Validation**: Community verification of detection accuracy
- **Sample Contribution**: User-submitted training samples and corrections

### Advanced Analytics
- **Player Performance Metrics**: Character-specific statistics and tendencies  
- **Team Strategy Analysis**: Lineup optimization and matchup insights
- **Game Outcome Prediction**: ML models trained on historical game data

### Multi-Game Support  
- **Mario Superstar Baseball (GameCube)**: Current target
- **Mario Super Sluggers (Wii)**: Natural expansion target
- **Other Sports Games**: Apply techniques to different game franchises

---

## Getting Started with Next Phase

**Immediate Next Steps:**
1. Review current multi-template detection system (71.4% accuracy)
2. Begin UI mockups for sample collection interface
3. Research Streamlit/Flask options for rapid prototyping
4. Start collecting "out" audio samples from existing footage

**Success Metrics:**
- UI reduces sample collection time by 75%
- "Out" detection achieves >85% accuracy
- Combined system (chimes + outs) reaches 90%+ inning detection accuracy
- Database handles 100+ games with sub-second query performance

This roadmap provides a clear path from the current audio-only system to a comprehensive Mario Baseball analytics platform, with each phase building upon previous achievements while expanding capabilities systematically.