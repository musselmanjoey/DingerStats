"""
Simple debug to compare reference patterns and find why accuracy dropped.
"""

import librosa
import numpy as np
from scipy import signal
import soundfile as sf
from pathlib import Path
from audio_filtering import AudioFilter

def simple_correlation_test():
    """
    Compare official vs old reference patterns on known transition.
    """
    print("Simple Correlation Debug Test")
    print("=" * 35)
    
    # Load both reference patterns
    try:
        official_ref, sr = librosa.load("reference_sounds/official_inning_transition_pattern.wav", sr=22050)
        print(f"Official reference: {len(official_ref)/sr:.2f}s, RMS: {np.sqrt(np.mean(official_ref**2)):.4f}")
    except Exception as e:
        print(f"Official reference failed: {e}")
        return
    
    try:
        old_ref, sr = librosa.load("reference_sounds/refined_inning_transition_pattern.wav", sr=22050)
        print(f"Old refined pattern: {len(old_ref)/sr:.2f}s, RMS: {np.sqrt(np.mean(old_ref**2)):.4f}")
    except Exception as e:
        print(f"Old refined pattern failed: {e}")
        old_ref = None
    
    # Load known transition segment from original video (2:28 = 148s)
    print(f"\nTesting on known transition at 2:28...")
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    audio_data, audio_sr = librosa.load(audio_file, sr=22050, offset=145, duration=6)  # 6 seconds around 2:28
    
    print(f"Test segment: {len(audio_data)/audio_sr:.1f}s loaded")
    
    # Test with no filtering first
    print(f"\nTesting correlation WITHOUT filtering:")
    
    # Official reference
    ref1_norm = official_ref / np.max(np.abs(official_ref))
    audio_norm = audio_data / np.max(np.abs(audio_data))
    corr1 = signal.correlate(audio_norm, ref1_norm, mode='valid')
    max_corr1 = np.max(corr1) / len(ref1_norm)
    print(f"Official reference: Max correlation = {max_corr1:.6f}")
    
    # Old reference (if available)
    if old_ref is not None:
        ref2_norm = old_ref / np.max(np.abs(old_ref))
        corr2 = signal.correlate(audio_norm, ref2_norm, mode='valid')
        max_corr2 = np.max(corr2) / len(ref2_norm)
        print(f"Old refined pattern: Max correlation = {max_corr2:.6f}")
    
    # Test with frequency filtering (user said spectral was best, but let's try frequency too)
    print(f"\nTesting with frequency filtering:")
    
    filter_system = AudioFilter()
    audio_filtered = filter_system.frequency_band_filter(audio_data)
    audio_filt_norm = audio_filtered / np.max(np.abs(audio_filtered))
    
    # Official reference with filtering
    corr1_filt = signal.correlate(audio_filt_norm, ref1_norm, mode='valid')
    max_corr1_filt = np.max(corr1_filt) / len(ref1_norm)
    print(f"Official reference: Max correlation = {max_corr1_filt:.6f}")
    
    # Old reference with filtering
    if old_ref is not None:
        corr2_filt = signal.correlate(audio_filt_norm, ref2_norm, mode='valid')
        max_corr2_filt = np.max(corr2_filt) / len(ref2_norm)
        print(f"Old refined pattern: Max correlation = {max_corr2_filt:.6f}")
    
    # Save debug files for listening
    debug_dir = Path("simple_debug")
    debug_dir.mkdir(exist_ok=True)
    
    sf.write(str(debug_dir / "test_segment_original.wav"), audio_data, audio_sr)
    sf.write(str(debug_dir / "test_segment_filtered.wav"), audio_filtered, audio_sr)
    sf.write(str(debug_dir / "official_reference.wav"), official_ref, sr)
    if old_ref is not None:
        sf.write(str(debug_dir / "old_reference.wav"), old_ref, sr)
    
    print(f"\nDebug files saved to: {debug_dir}")
    print("Listen to compare the references against the test segment!")
    
    # Quick test with different thresholds on original video
    print(f"\nQuick threshold test on original video (first 10 minutes):")
    
    # Use the better reference pattern
    if old_ref is not None and max_corr2_filt > max_corr1_filt:
        print("Using old refined pattern (better correlation)")
        best_ref = old_ref
    else:
        print("Using official reference pattern")
        best_ref = official_ref
    
    # Load more of original video
    full_audio, full_sr = librosa.load(audio_file, sr=22050, duration=600)  # 10 minutes
    full_filtered = filter_system.frequency_band_filter(full_audio)
    
    # Correlation
    ref_norm = best_ref / np.max(np.abs(best_ref))
    full_norm = full_filtered / np.max(np.abs(full_filtered))
    full_corr = signal.correlate(full_norm, ref_norm, mode='valid')
    full_corr = full_corr / len(ref_norm)
    
    print(f"Full correlation range: {np.min(full_corr):.6f} to {np.max(full_corr):.6f}")
    
    # Test a few thresholds
    known_times = [148, 199, 243, 314]  # First 4 within 10 minutes
    
    for percentile in [99.5, 99.0, 98.5, 98.0]:
        threshold = np.percentile(full_corr, percentile)
        peaks, _ = signal.find_peaks(full_corr, height=threshold, distance=int(90 * full_sr))
        
        detections = [(idx / full_sr, full_corr[idx]) for idx in peaks]
        
        # Check accuracy
        found = 0
        for known_time in known_times:
            close = [t for t, s in detections if abs(t - known_time) <= 10]
            if close:
                found += 1
        
        accuracy = found / len(known_times)
        print(f"  {percentile:4.1f}% threshold: {len(detections):2d} detections, {accuracy:.1%} accuracy")

if __name__ == "__main__":
    simple_correlation_test()