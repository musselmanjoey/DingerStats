"""
Full Video Analysis - Find all inning transitions in the complete video
"""

from robust_search_system import RobustInningDetector

def analyze_full_video():
    """Analyze the complete video for all inning transitions."""
    print("FULL VIDEO INNING ANALYSIS")
    print("=" * 70)
    
    detector = RobustInningDetector()
    
    if not detector.load_reference():
        return
    
    video_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    
    # Get total video duration first
    import librosa
    audio_data, sr = librosa.load(video_file, sr=22050)
    total_duration = len(audio_data) / sr
    total_minutes = total_duration / 60
    
    print(f"Video duration: {total_minutes:.1f} minutes ({total_duration:.0f} seconds)")
    
    # Run blind search on full video
    detections = detector.full_video_search_improved(video_file, None)
    
    print(f"\nCOMPLETE INNING TRANSITION ANALYSIS:")
    print("=" * 50)
    
    if not detections:
        print("No inning transitions detected!")
        return
    
    # Sort detections by time (not score) for proper chronological analysis
    detections_by_time = sorted(detections, key=lambda x: x[0])
    
    print(f"Found {len(detections)} inning transitions (sorted chronologically):")
    
    # Analyze the complete game structure
    inning_count = 0
    half_inning_count = 0
    
    for i, (time_sec, score) in enumerate(detections_by_time):
        mm, ss = int(time_sec // 60), int(time_sec % 60)
        
        # Determine inning structure
        half_inning_count += 1
        
        # Each pair of transitions represents one complete inning
        if half_inning_count % 2 == 0:
            inning_count += 1
            inning_status = f"End of Inning {inning_count}"
        else:
            inning_status = f"Middle of Inning {inning_count + 1}"
        
        print(f"  {i+1:2d}: {mm:2d}:{ss:02d} ({time_sec:6.1f}s) - {inning_status} - Score: {score:.6f}")
    
    # Calculate game structure
    complete_innings = half_inning_count // 2
    partial_innings = half_inning_count % 2
    
    print(f"\nGAME STRUCTURE ANALYSIS:")
    print(f"Total transitions detected: {len(detections)}")
    print(f"Complete innings played: {complete_innings}")
    if partial_innings:
        print(f"Partial inning in progress: +0.5")
        total_innings_played = complete_innings + 0.5
    else:
        print(f"Game ended after complete inning")
        total_innings_played = complete_innings
    
    print(f"Total innings of gameplay: {total_innings_played}")
    
    # Analyze timing between innings
    if len(detections_by_time) >= 2:
        times = [time for time, score in detections_by_time]
        gaps = [times[i+1] - times[i] for i in range(len(times)-1)]
        
        print(f"\nINNING TIMING ANALYSIS:")
        print(f"Average time per half-inning: {sum(gaps)/len(gaps)/60:.1f} minutes")
        print(f"Shortest half-inning: {min(gaps)/60:.1f} minutes")
        print(f"Longest half-inning: {max(gaps)/60:.1f} minutes")
        
        # Estimate total game time
        if len(times) > 0:
            game_start = times[0]  # First transition
            game_end = times[-1]   # Last transition
            active_gameplay_time = (game_end - game_start) / 60
            print(f"Active gameplay duration: {active_gameplay_time:.1f} minutes")
    
    # Validate against our known transitions
    known_transitions = [148, 199, 243, 314, 454]
    print(f"\nVALIDATION AGAINST KNOWN TRANSITIONS:")
    found_count = 0
    tolerance = 15.0
    
    for expected in known_transitions:
        mm_exp, ss_exp = int(expected // 60), int(expected % 60)
        
        matches = [(t, s) for t, s in detections if abs(t - expected) <= tolerance]
        
        if matches:
            best_match = max(matches, key=lambda x: x[1])
            match_time, match_score = best_match
            mm_match, ss_match = int(match_time // 60), int(match_time % 60)
            error = abs(match_time - expected)
            
            print(f"  [FOUND] {mm_exp}:{ss_exp:02d} -> {mm_match}:{ss_match:02d} "
                  f"(error: {error:.1f}s, score: {match_score:.6f})")
            found_count += 1
        else:
            print(f"  [MISSED] {mm_exp}:{ss_exp:02d}")
    
    accuracy = found_count / len(known_transitions)
    print(f"\nOverall accuracy: {accuracy:.1%} ({found_count}/{len(known_transitions)} known transitions found)")
    
    return detections, total_innings_played

if __name__ == "__main__":
    analyze_full_video()