"""
Test inning detection on the already downloaded new video.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path

def test_downloaded_video():
    """
    Test our pattern matching on the downloaded Monty Mole video.
    """
    print("Testing Inning Detection on New Video")
    print("=" * 45)
    
    # Find the downloaded file
    temp_dir = Path("temp_audio_new")
    audio_files = list(temp_dir.glob("*.webm"))
    
    if not audio_files:
        print("No downloaded video found!")
        return
    
    audio_file = str(audio_files[0])
    print(f"Testing downloaded Mario Baseball video ({len(audio_files[0].name)} character filename)")
    
    # Load our reference pattern
    print("\n1. Loading reference pattern...")
    try:
        pattern_file = "reference_sounds/refined_inning_transition_pattern.wav"
        reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
        print(f"   Reference loaded: {len(reference_pattern)/ref_sr:.2f}s")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Load new video audio (first 10 minutes)
    print("\n2. Loading new video audio...")
    try:
        audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=600)  # 10 minutes
        print(f"   Audio loaded: {len(audio_data)/audio_sr/60:.1f} minutes")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    # Apply pattern matching
    print("\n3. Applying pattern matching...")
    
    # Normalize (same method that gave us 100% accuracy)
    ref_normalized = reference_pattern / np.max(np.abs(reference_pattern))
    audio_normalized = audio_data / np.max(np.abs(audio_data))
    
    # Cross-correlation
    correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
    correlation = correlation / len(ref_normalized)
    
    print(f"   Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
    
    # Find peaks
    threshold = np.percentile(correlation, 99.5)  # Top 0.5%
    min_gap = int(20 * audio_sr)  # 20 seconds
    
    peaks, _ = signal.find_peaks(correlation, height=threshold, distance=min_gap)
    
    # Convert to times
    matches = []
    for idx in peaks:
        time_sec = idx / audio_sr
        score = correlation[idx]
        matches.append((time_sec, score))
    
    matches.sort(key=lambda x: x[1], reverse=True)
    
    print(f"   Found {len(matches)} potential inning transitions")
    
    # Show results
    print("\n4. RESULTS:")
    if matches:
        print("   Detected inning transitions:")
        for i, (time, score) in enumerate(matches[:8]):
            mm = int(time // 60)
            ss = int(time % 60)
            print(f"   {i+1}: {mm:2d}:{ss:02d} ({time:6.1f}s) - Score: {score:.6f}")
        
        # Quick analysis
        if len(matches) >= 3:
            print(f"\n   [SUCCESS] Found {len(matches)} transitions - system working!")
        elif len(matches) >= 1:
            print(f"\n   [PARTIAL] Found {len(matches)} transitions - needs investigation")
        else:
            print(f"\n   [NONE] No transitions found - pattern may not match")
    else:
        print("   No clear inning transitions detected")
        print(f"   Max correlation: {np.max(correlation):.6f}")
        print(f"   Threshold used: {threshold:.6f}")
        
        # Try lower threshold
        low_threshold = np.percentile(correlation, 95)
        low_peaks, _ = signal.find_peaks(correlation, height=low_threshold, distance=min_gap)
        print(f"   With lower threshold ({low_threshold:.6f}): {len(low_peaks)} peaks")
    
    return matches

if __name__ == "__main__":
    test_downloaded_video()