"""
Quick test of pattern matching with optimized processing.
"""

import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path

def quick_pattern_test():
    """
    Test pattern matching on a smaller audio segment for faster results.
    """
    print("Quick Pattern Matching Test")
    print("=" * 40)
    
    # Load reference pattern
    print("Loading reference pattern...")
    try:
        pattern_file = "reference_sounds/inning_transition_average_pattern.wav"
        reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
        print(f"[SUCCESS] Reference loaded: {len(reference_pattern)/ref_sr:.2f}s, {len(reference_pattern):,} samples")
    except Exception as e:
        print(f"[ERROR] Failed to load reference: {e}")
        return
    
    # Load audio (first 8 minutes to include our 3 known transitions)
    print("\nLoading test audio (first 8 minutes)...")
    try:
        audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
        audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=480)  # 8 minutes
        print(f"[SUCCESS] Audio loaded: {len(audio_data)/audio_sr:.1f}s, {len(audio_data):,} samples")
    except Exception as e:
        print(f"[ERROR] Failed to load audio: {e}")
        return
    
    # Normalize signals
    print("\nNormalizing signals...")
    ref_normalized = reference_pattern / np.max(np.abs(reference_pattern))
    audio_normalized = audio_data / np.max(np.abs(audio_data))
    
    # Compute correlation (optimized)
    print("Computing cross-correlation...")
    correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
    correlation = correlation / len(ref_normalized)  # Normalize
    
    print(f"[SUCCESS] Correlation computed: {len(correlation):,} values")
    print(f"  Max correlation: {np.max(correlation):.4f}")
    print(f"  Mean correlation: {np.mean(correlation):.4f}")
    
    # Find peaks
    print("\nFinding peaks...")
    correlation_threshold = 0.15  # Lower threshold
    min_gap_samples = int(30 * audio_sr)  # 30 seconds minimum gap
    
    peak_indices, properties = signal.find_peaks(
        correlation,
        height=correlation_threshold,
        distance=min_gap_samples
    )
    
    print(f"Found {len(peak_indices)} peaks above {correlation_threshold}")
    
    # Convert to times and scores
    matches = []
    for idx in peak_indices:
        time_seconds = idx / audio_sr
        correlation_score = correlation[idx]
        matches.append((time_seconds, correlation_score))
    
    # Sort by score
    matches.sort(key=lambda x: x[1], reverse=True)
    
    # Display results
    print(f"\nTOP MATCHES:")
    for i, (time, score) in enumerate(matches[:10]):
        minutes = int(time // 60)
        seconds = int(time % 60)
        print(f"  {i+1}: {minutes:2d}:{seconds:02d} ({time:6.1f}s) - Score: {score:.4f}")
    
    # Check against known times
    known_times = [148, 243, 454]  # 2:28, 4:03, 7:34
    print(f"\nVALIDATION (Known times: 2:28, 4:03, 7:34):")
    
    tolerance = 5.0  # 5 second tolerance
    found_count = 0
    
    for known_time in known_times:
        if known_time > 480:  # Skip if beyond our 8-minute test
            continue
            
        known_mm = int(known_time // 60)
        known_ss = int(known_time % 60)
        
        # Find closest match
        close_matches = [
            (time, score) for time, score in matches
            if abs(time - known_time) <= tolerance
        ]
        
        if close_matches:
            best_match = max(close_matches, key=lambda x: x[1])
            match_time, match_score = best_match
            match_mm = int(match_time // 60)
            match_ss = int(match_time % 60)
            error = abs(match_time - known_time)
            
            print(f"  [FOUND] {known_mm:2d}:{known_ss:02d} -> {match_mm:2d}:{match_ss:02d} (error: {error:.1f}s, score: {match_score:.4f})")
            found_count += 1
        else:
            print(f"  [MISSED] {known_mm:2d}:{known_ss:02d} -> NOT FOUND")
    
    # Summary
    known_in_range = len([t for t in known_times if t <= 480])
    accuracy = found_count / known_in_range if known_in_range > 0 else 0
    
    print(f"\nRESULTS:")
    print(f"  Found: {found_count}/{known_in_range} known transitions")
    print(f"  Accuracy: {accuracy:.1%}")
    
    if accuracy >= 0.8:
        print("  [EXCELLENT] Pattern matching is working well!")
    elif accuracy >= 0.5:
        print("  [GOOD] May need minor threshold tuning")
    else:
        print("  [NEEDS WORK] Consider adjusting parameters")
    
    return matches, correlation

if __name__ == "__main__":
    quick_pattern_test()