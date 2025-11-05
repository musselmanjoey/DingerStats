"""
Test inning detection with progressively more selective thresholds
to target exactly 9 inning transitions for a full game.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path

def test_selective_detection():
    """
    Test with increasingly selective thresholds to find optimal detection level.
    """
    print("Testing Selective Inning Detection")
    print("=" * 40)
    print("Goal: Find ~9 inning transitions for a full game")
    
    # Find the downloaded file
    temp_dir = Path("temp_audio_new")
    audio_files = list(temp_dir.glob("*.webm"))
    
    if not audio_files:
        print("No downloaded video found!")
        return
    
    audio_file = str(audio_files[0])
    
    # Load reference pattern and audio
    print("\n1. Loading reference pattern and audio...")
    try:
        pattern_file = "reference_sounds/refined_inning_transition_pattern.wav"
        reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
        
        # Load full video (not just 10 minutes) to capture all 9 innings
        audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=1800)  # 30 minutes max
        duration_minutes = len(audio_data) / audio_sr / 60
        
        print(f"   Reference pattern: {len(reference_pattern)/ref_sr:.2f}s")
        print(f"   Video audio: {duration_minutes:.1f} minutes loaded")
        
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Compute correlation once
    print("\n2. Computing cross-correlation...")
    ref_normalized = reference_pattern / np.max(np.abs(reference_pattern))
    audio_normalized = audio_data / np.max(np.abs(audio_data))
    
    correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
    correlation = correlation / len(ref_normalized)
    
    print(f"   Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
    
    # Test multiple threshold levels
    print("\n3. Testing different selectivity levels...")
    
    threshold_levels = [99.9, 99.8, 99.5, 99.0, 98.5, 98.0, 97.0, 95.0]  # Percentiles
    min_gap_samples = int(60 * audio_sr)  # 1 minute minimum gap (more realistic for innings)
    
    best_results = None
    best_threshold = None
    
    for percentile in threshold_levels:
        threshold = np.percentile(correlation, percentile)
        
        # Find peaks
        peaks, _ = signal.find_peaks(correlation, height=threshold, distance=min_gap_samples)
        
        # Convert to times
        matches = []
        for idx in peaks:
            time_sec = idx / audio_sr
            score = correlation[idx]
            matches.append((time_sec, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   {percentile:4.1f}th percentile (threshold {threshold:.6f}): {len(matches):2d} matches")
        
        # Show top matches for this threshold
        if len(matches) > 0:
            top_3 = matches[:3]
            times_str = ", ".join([f"{int(t//60)}:{int(t%60):02d}" for t, s in top_3])
            print(f"        Top matches: {times_str}")
        
        # Track the best result (closest to 9 transitions)
        if best_results is None or abs(len(matches) - 9) < abs(len(best_results) - 9):
            best_results = matches
            best_threshold = percentile
    
    # Show detailed results for the best threshold
    print(f"\n4. BEST THRESHOLD ANALYSIS")
    print(f"   Selected: {best_threshold}th percentile")
    print(f"   Detected: {len(best_results)} transitions (target: 9)")
    
    if best_results:
        print(f"\n   Detected inning transitions:")
        for i, (time, score) in enumerate(best_results):
            mm = int(time // 60)
            ss = int(time % 60)
            print(f"   {i+1:2d}: {mm:2d}:{ss:02d} ({time:6.1f}s) - Score: {score:.6f}")
        
        # Analyze timing pattern
        if len(best_results) >= 2:
            times_only = [time for time, score in best_results]
            gaps = [times_only[i+1] - times_only[i] for i in range(len(times_only)-1)]
            avg_gap = np.mean(gaps)
            
            print(f"\n   Timing Analysis:")
            print(f"   Average gap between transitions: {avg_gap:.1f}s ({avg_gap/60:.1f} minutes)")
            print(f"   Gap range: {min(gaps):.1f}s to {max(gaps):.1f}s")
            
            # Check if timing makes sense for baseball innings
            if 120 <= avg_gap <= 300:  # 2-5 minutes per inning seems reasonable
                print(f"   [REASONABLE] Gap timing makes sense for baseball innings")
            else:
                print(f"   [QUESTIONABLE] Gap timing seems off for baseball innings")
    
    # Final assessment
    print(f"\n5. ASSESSMENT:")
    transition_count = len(best_results)
    
    if 8 <= transition_count <= 10:
        print(f"   [EXCELLENT] Found {transition_count} transitions - very close to 9 innings!")
        status = "READY FOR VALIDATION"
    elif 5 <= transition_count <= 12:
        print(f"   [GOOD] Found {transition_count} transitions - reasonable for baseball game")
        status = "NEEDS MANUAL VERIFICATION"
    elif transition_count > 15:
        print(f"   [TOO MANY] Found {transition_count} transitions - likely false positives")
        status = "THRESHOLD TOO LOW"
    elif transition_count < 3:
        print(f"   [TOO FEW] Found {transition_count} transitions - missing real ones")  
        status = "THRESHOLD TOO HIGH"
    else:
        print(f"   [UNCLEAR] Found {transition_count} transitions - needs investigation")
        status = "NEEDS TUNING"
    
    print(f"   Status: {status}")
    
    if status == "READY FOR VALIDATION":
        print(f"\n   Next step: Manually check a few timestamps to verify accuracy")
    elif status == "NEEDS MANUAL VERIFICATION":
        print(f"\n   Next step: Spot-check timestamps against actual video")
    
    return best_results, best_threshold

if __name__ == "__main__":
    test_selective_detection()