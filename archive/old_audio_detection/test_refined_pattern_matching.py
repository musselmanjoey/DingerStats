"""
Test the refined pattern matching to see if we can now detect the 4:03 transition.
"""

import librosa
import numpy as np
from scipy import signal

def test_refined_pattern_matching():
    """
    Test pattern matching with the refined pattern from expanded analysis.
    """
    print("Testing Refined Pattern Matching")
    print("=" * 40)
    print("Using refined pattern from expanded window analysis")
    
    # Known transitions with refined timing
    known_transitions = [
        {"original": "2:28", "refined": "2:27", "time_seconds": 147, "description": "Top 1st to Bottom 1st"},
        {"original": "3:19", "refined": "3:18", "time_seconds": 198, "description": "Bottom 1st to Top 2nd"}, 
        {"original": "4:03", "refined": "4:02", "time_seconds": 242, "description": "Top 2nd to Bottom 2nd - MISSING TARGET"},
        {"original": "5:14", "refined": "5:13", "time_seconds": 313, "description": "Bottom 2nd to Top 3rd"},
        {"original": "7:34", "refined": "7:35", "time_seconds": 455, "description": "Top 3rd to Bottom 3rd"},
    ]
    
    # Load refined reference pattern
    print("\n1. Loading refined reference pattern...")
    try:
        pattern_file = "reference_sounds/refined_inning_transition_pattern.wav"
        reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
        print(f"   [SUCCESS] Refined pattern loaded: {len(reference_pattern)/ref_sr:.2f}s")
        print(f"   RMS: {np.sqrt(np.mean(reference_pattern**2)):.4f}")
    except Exception as e:
        print(f"   [ERROR] Failed to load refined pattern: {e}")
        return
    
    # Load test audio
    print("\n2. Loading test audio (first 8 minutes)...")
    try:
        audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
        audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=480)
        print(f"   [SUCCESS] Audio loaded: {len(audio_data)/audio_sr:.1f}s")
    except Exception as e:
        print(f"   [ERROR] Failed to load audio: {e}")
        return
    
    # Test with standard max normalization (which worked best before)
    print(f"\n3. Computing cross-correlation with refined pattern...")
    
    # Normalize signals  
    ref_normalized = reference_pattern / np.max(np.abs(reference_pattern))
    audio_normalized = audio_data / np.max(np.abs(audio_data))
    
    # Compute cross-correlation
    correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
    correlation = correlation / len(ref_normalized)
    
    print(f"   Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
    
    # Find peaks with adaptive threshold
    correlation_threshold = np.percentile(correlation, 99.5)  # Top 0.5%
    min_gap_samples = int(20 * audio_sr)  # 20 seconds minimum gap
    
    peak_indices, _ = signal.find_peaks(
        correlation,
        height=correlation_threshold,
        distance=min_gap_samples
    )
    
    # Convert to times and scores
    matches = []
    for idx in peak_indices:
        time_seconds = idx / audio_sr
        score = correlation[idx]
        matches.append((time_seconds, score))
    
    # Sort by score
    matches.sort(key=lambda x: x[1], reverse=True)
    
    print(f"   Found {len(matches)} peaks above threshold {correlation_threshold:.6f}")
    
    # Show top matches
    print(f"\n4. Top correlation matches:")
    for i, (time, score) in enumerate(matches[:10]):
        mm = int(time // 60)
        ss = int(time % 60)
        print(f"   {i+1}: {mm:2d}:{ss:02d} ({time:6.1f}s) - Score: {score:.6f}")
    
    # Check against known transitions with wider tolerance
    print(f"\n5. Validation against known transitions:")
    tolerance = 8.0  # Increased tolerance since we have timing adjustments
    found_count = 0
    
    for known in known_transitions:
        original_time = known["original"]
        refined_time = known["refined"]
        target_time = known["time_seconds"]
        description = known["description"]
        is_missing_target = "MISSING TARGET" in description
        
        # Check both original and refined timing
        original_seconds = int(original_time.split(':')[0]) * 60 + int(original_time.split(':')[1])
        
        # Find matches near either original or refined timing
        close_matches = []
        for time, score in matches:
            if (abs(time - original_seconds) <= tolerance or 
                abs(time - target_time) <= tolerance):
                close_matches.append((time, score))
        
        if close_matches:
            best_match = max(close_matches, key=lambda x: x[1])
            match_time, match_score = best_match
            match_mm = int(match_time // 60)
            match_ss = int(match_time % 60)
            error_original = abs(match_time - original_seconds)
            error_refined = abs(match_time - target_time)
            
            status = "[FOUND]"
            if is_missing_target:
                status = "[FOUND - WAS MISSING!]"
            
            print(f"   {status} {original_time} -> {match_mm:2d}:{match_ss:02d}")
            print(f"            Error from original: {error_original:.1f}s, from refined: {error_refined:.1f}s")
            print(f"            Score: {match_score:.6f} - {description}")
            found_count += 1
        else:
            status = "[MISSED]" 
            if is_missing_target:
                status = "[STILL MISSING]"
            print(f"   {status} {original_time} - {description}")
    
    # Calculate results
    accuracy = found_count / len(known_transitions)
    
    print(f"\n6. RESULTS SUMMARY:")
    print(f"   Transitions found: {found_count}/{len(known_transitions)}")
    print(f"   Detection accuracy: {accuracy:.1%}")
    print(f"   Total correlation peaks: {len(matches)}")
    
    if accuracy > 0.8:  # Previous accuracy
        print(f"   [IMPROVED] Better than before!")
    elif accuracy == 0.8:
        print(f"   [SAME] Same as before, but hopefully found 4:03!")
    else:
        print(f"   [WORSE] Lower accuracy than before")
    
    # Specific check for 4:03 
    print(f"\n7. SPECIFIC CHECK FOR 4:03 TRANSITION:")
    target_4_03 = 4*60 + 3  # 243 seconds
    refined_4_03 = 4*60 + 2  # 242 seconds (refined location)
    
    matches_near_4_03 = [
        (time, score) for time, score in matches 
        if abs(time - target_4_03) <= 10 or abs(time - refined_4_03) <= 10
    ]
    
    if matches_near_4_03:
        print(f"   [SUCCESS] Found {len(matches_near_4_03)} matches near 4:03!")
        for time, score in matches_near_4_03:
            mm = int(time // 60)
            ss = int(time % 60)
            error_original = abs(time - target_4_03)
            error_refined = abs(time - refined_4_03)
            print(f"     {mm:2d}:{ss:02d} - Score: {score:.6f} (errors: {error_original:.1f}s/{error_refined:.1f}s)")
    else:
        print(f"   [STILL MISSING] No matches found near 4:03 area")
        
        # Debug: Check correlation values around 4:03
        start_idx = int((target_4_03 - 10) * audio_sr)
        end_idx = int((target_4_03 + 10) * audio_sr)
        if start_idx >= 0 and end_idx < len(correlation):
            local_correlation = correlation[start_idx:end_idx]
            local_max = np.max(local_correlation)
            local_max_idx = np.argmax(local_correlation) + start_idx
            local_max_time = local_max_idx / audio_sr
            
            print(f"     Debug: Max correlation near 4:03: {local_max:.6f} at {local_max_time/60:.1f}:{int(local_max_time%60):02d}")
            print(f"     Debug: Threshold was: {correlation_threshold:.6f}")
            
            if local_max < correlation_threshold:
                print(f"     Issue: Peak too low for threshold - consider lowering threshold")
    
    return matches, accuracy

if __name__ == "__main__":
    matches, accuracy = test_refined_pattern_matching()