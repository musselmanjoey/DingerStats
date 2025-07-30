"""
Test improved pattern matching with all 5 inning transition examples.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path

def test_improved_pattern_matching():
    """
    Test pattern matching using the improved reference pattern based on all 5 examples.
    """
    print("Testing Improved Pattern Matching System")
    print("=" * 50)
    
    # All 5 known transition times for validation
    known_transitions = [
        {"time_mm_ss": "2:28", "time_seconds": 148, "description": "Top 1st to Bottom 1st"},
        {"time_mm_ss": "3:19", "time_seconds": 199, "description": "Bottom 1st to Top 2nd"}, 
        {"time_mm_ss": "4:03", "time_seconds": 243, "description": "Top 2nd to Bottom 2nd"},
        {"time_mm_ss": "5:14", "time_seconds": 314, "description": "Bottom 2nd to Top 3rd"},
        {"time_mm_ss": "7:34", "time_seconds": 454, "description": "Top 3rd to Bottom 3rd"},
    ]
    
    # Load improved reference pattern
    print("1. Loading improved reference pattern...")
    try:
        pattern_file = "reference_sounds/improved_inning_transition_pattern.wav"
        reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
        print(f"   [SUCCESS] Pattern loaded: {len(reference_pattern)/ref_sr:.2f}s, RMS: {np.sqrt(np.mean(reference_pattern**2)):.4f}")
    except Exception as e:
        print(f"   [ERROR] Failed to load pattern: {e}")
        return
    
    # Load test audio (first 8 minutes to include all 5 transitions)
    print("\n2. Loading test audio (first 8 minutes)...")
    try:
        audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
        audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=480)  # 8 minutes
        print(f"   [SUCCESS] Audio loaded: {len(audio_data)/audio_sr:.1f}s")
    except Exception as e:
        print(f"   [ERROR] Failed to load audio: {e}")
        return
    
    # Test multiple normalization methods
    normalization_methods = [
        ("Standard (max)", lambda x: x / np.max(np.abs(x))),
        ("Z-score", lambda x: (x - np.mean(x)) / np.std(x)),
        ("RMS", lambda x: x / np.sqrt(np.mean(x**2))),
    ]
    
    print(f"\n3. Testing different normalization methods...")
    
    best_method = None
    best_accuracy = 0
    best_matches = []
    
    for method_name, normalize_func in normalization_methods:
        print(f"\n   Testing {method_name} normalization:")
        
        # Normalize signals
        try:
            ref_normalized = normalize_func(reference_pattern)
            audio_normalized = normalize_func(audio_data)
        except:
            print(f"   [ERROR] Normalization failed for {method_name}")
            continue
        
        # Compute cross-correlation
        correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
        correlation = correlation / len(ref_normalized)
        
        print(f"   Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
        
        # Find peaks with low threshold
        correlation_threshold = np.percentile(correlation, 99.5)  # Top 0.5% of correlation values
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
        
        print(f"   Found {len(matches)} peaks above {correlation_threshold:.6f}")
        
        # Validate against known transitions
        tolerance = 5.0  # 5 second tolerance
        found_count = 0
        
        for known in known_transitions:
            known_time = known["time_seconds"]
            if known_time > 480:  # Skip if beyond 8 minutes
                continue
                
            # Find closest match
            close_matches = [
                (time, score) for time, score in matches
                if abs(time - known_time) <= tolerance
            ]
            
            if close_matches:
                found_count += 1
        
        accuracy = found_count / len(known_transitions)
        print(f"   Accuracy: {accuracy:.1%} ({found_count}/{len(known_transitions)} found)")
        
        # Track best method
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_method = method_name
            best_matches = matches.copy()
    
    # Detailed analysis of best method
    print(f"\n4. DETAILED ANALYSIS - Best Method: {best_method}")
    print(f"   Overall Accuracy: {best_accuracy:.1%}")
    
    print(f"\n   Top matches:")
    for i, (time, score) in enumerate(best_matches[:10]):
        mm = int(time // 60)
        ss = int(time % 60)
        print(f"   {i+1}: {mm:2d}:{ss:02d} ({time:6.1f}s) - Score: {score:.6f}")
    
    print(f"\n   Validation against known transitions:")
    tolerance = 5.0
    
    for known in known_transitions:
        known_time = known["time_seconds"]
        known_mm_ss = known["time_mm_ss"]
        description = known["description"]
        
        if known_time > 480:  # Skip if beyond test duration
            print(f"   {known_mm_ss} - {description} -> BEYOND TEST RANGE")
            continue
        
        # Find closest match
        close_matches = [
            (time, score) for time, score in best_matches
            if abs(time - known_time) <= tolerance
        ]
        
        if close_matches:
            best_match = max(close_matches, key=lambda x: x[1])
            match_time, match_score = best_match
            match_mm = int(match_time // 60)
            match_ss = int(match_time % 60)
            error = abs(match_time - known_time)
            
            print(f"   {known_mm_ss} - {description}")
            print(f"        -> FOUND: {match_mm:2d}:{match_ss:02d} (error: {error:.1f}s, score: {match_score:.6f})")
        else:
            print(f"   {known_mm_ss} - {description}")
            print(f"        -> MISSED: No match within {tolerance}s")
    
    # Final summary
    print(f"\n5. SUMMARY:")
    print(f"   Best normalization method: {best_method}")
    print(f"   Detection accuracy: {best_accuracy:.1%}")
    print(f"   Total matches found: {len(best_matches)}")
    
    if best_accuracy >= 0.8:
        print(f"   [EXCELLENT] Pattern matching working well!")
        print(f"   Ready for full video processing!")
    elif best_accuracy >= 0.6:
        print(f"   [GOOD] Significant improvement! May need minor tuning.")
    elif best_accuracy > 0:
        print(f"   [PROGRESS] Better than before, but needs more work.")
    else:
        print(f"   [NEEDS WORK] Still not detecting the patterns.")
    
    return best_matches, best_method, best_accuracy

if __name__ == "__main__":
    test_improved_pattern_matching()