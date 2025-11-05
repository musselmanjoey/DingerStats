"""
Debug the final pattern matching system to understand why accuracy dropped.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path
from audio_filtering import AudioFilter
import soundfile as sf

def debug_correlation_comparison():
    """
    Compare different reference patterns to understand the accuracy drop.
    """
    print("Debugging Pattern Matching System")
    print("=" * 40)
    
    # Load different reference patterns
    reference_patterns = {}
    
    # 1. Official "Next Inning" pattern
    try:
        official_ref, sr = librosa.load("reference_sounds/official_inning_transition_pattern.wav", sr=22050)
        reference_patterns["Official Next Inning"] = official_ref
        print(f"✓ Official reference: {len(official_ref)/sr:.2f}s")
    except Exception as e:
        print(f"✗ Official reference failed: {e}")
    
    # 2. Our old refined pattern
    try:
        old_ref, sr = librosa.load("reference_sounds/refined_inning_transition_pattern.wav", sr=22050)
        reference_patterns["Old Refined Pattern"] = old_ref
        print(f"✓ Old refined pattern: {len(old_ref)/sr:.2f}s")
    except Exception as e:
        print(f"✗ Old refined pattern failed: {e}")
    
    # 3. Test on known good segment from original video
    print(f"\nTesting on known transition at 2:28 (148s)...")
    
    try:
        # Load the original video
        audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
        audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=600)  # First 10 minutes
        
        # Extract known transition segment (2:28 = 148s)
        known_start = 145  # 3 seconds before
        known_end = 151    # 3 seconds after
        start_sample = int(known_start * audio_sr)
        end_sample = int(known_end * audio_sr)
        known_segment = audio_data[start_sample:end_sample]
        
        print(f"Known segment extracted: {len(known_segment)/audio_sr:.1f}s")
        
        # Test different filtering approaches on this segment
        filter_system = AudioFilter()
        
        # No filtering
        segment_original = known_segment
        
        # Spectral filtering only
        filter_config_spectral = {"spectral_subtraction": True, "frequency_band": False, "compression": False, "noise_gate": False}
        segment_spectral = filter_system.apply_combined_filter(known_segment, filter_config_spectral)
        
        # Frequency filtering only  
        filter_config_freq = {"spectral_subtraction": False, "frequency_band": True, "compression": False, "noise_gate": False}
        segment_frequency = filter_system.apply_combined_filter(known_segment, filter_config_freq)
        
        # Combined light filtering
        filter_config_combined = {"spectral_subtraction": True, "frequency_band": True, "compression": False, "noise_gate": False}
        segment_combined = filter_system.apply_combined_filter(known_segment, filter_config_combined)
        
        test_segments = {
            "Original (no filter)": segment_original,
            "Spectral only": segment_spectral,
            "Frequency only": segment_frequency,
            "Combined light": segment_combined
        }
        
        print(f"\nCORRELATION TEST RESULTS:")
        print("-" * 50)
        
        # Test each reference pattern against each filtered segment
        for ref_name, ref_pattern in reference_patterns.items():
            print(f"\nReference: {ref_name}")
            
            for segment_name, test_segment in test_segments.items():
                # Normalize both
                ref_norm = ref_pattern / np.max(np.abs(ref_pattern))
                seg_norm = test_segment / np.max(np.abs(test_segment))
                
                # Cross-correlation
                correlation = signal.correlate(seg_norm, ref_norm, mode='valid')
                max_corr = np.max(correlation) / len(ref_norm)
                
                print(f"  vs {segment_name:<20}: {max_corr:.6f}")
        
        # Save the best combinations for manual listening
        print(f"\nSaving test segments for manual verification...")
        debug_dir = Path("debug_correlation")
        debug_dir.mkdir(exist_ok=True)
        
        for segment_name, segment in test_segments.items():
            filename = debug_dir / f"known_transition_{segment_name.lower().replace(' ', '_')}.wav"
            sf.write(str(filename), segment, audio_sr)
        
        # Also save reference patterns for comparison
        for ref_name, ref_pattern in reference_patterns.items():
            filename = debug_dir / f"reference_{ref_name.lower().replace(' ', '_')}.wav"
            sf.write(str(filename), ref_pattern, 22050)
        
        print(f"Debug files saved to: {debug_dir}")
        
    except Exception as e:
        print(f"Error in segment testing: {e}")
    
    print(f"\nRECOMMENDATIONS:")
    print("1. Listen to the debug files to compare reference patterns")
    print("2. Check which filtering approach preserves the target sound best")
    print("3. Consider if official reference needs adjustment")

def test_correlation_thresholds():
    """
    Test different correlation thresholds to find optimal detection.
    """
    print(f"\n" + "="*40)
    print("TESTING CORRELATION THRESHOLDS")
    print("="*40)
    
    # Use the best reference from above testing
    # For now, let's use the old refined pattern that gave us 80% accuracy
    try:
        reference_pattern, sr = librosa.load("reference_sounds/refined_inning_transition_pattern.wav", sr=22050)
        print(f"Using refined pattern: {len(reference_pattern)/sr:.2f}s")
    except:
        print("Falling back to official pattern")
        reference_pattern, sr = librosa.load("reference_sounds/official_inning_transition_pattern.wav", sr=22050)
    
    # Load original video
    audio_data, audio_sr = librosa.load("temp_audio/The CRAZIEST hit in Mario Baseball.webm", sr=22050, duration=600)
    
    # Apply light filtering (not as aggressive as spectral-only)
    filter_system = AudioFilter()
    filter_config = {"spectral_subtraction": False, "frequency_band": True, "compression": False, "noise_gate": False}
    filtered_audio = filter_system.apply_combined_filter(audio_data, filter_config)
    
    # Compute correlation
    ref_norm = reference_pattern / np.max(np.abs(reference_pattern))
    audio_norm = filtered_audio / np.max(np.abs(filtered_audio))
    correlation = signal.correlate(audio_norm, ref_norm, mode='valid')
    correlation = correlation / len(ref_norm)
    
    # Test different thresholds
    known_times = [148, 199, 243, 314, 454]  # Our 5 known transitions
    thresholds = [99.9, 99.8, 99.5, 99.0, 98.5, 98.0]
    
    print(f"Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
    
    for percentile in thresholds:
        threshold = np.percentile(correlation, percentile)
        
        # Find peaks
        peaks, _ = signal.find_peaks(correlation, height=threshold, distance=int(90 * audio_sr))
        
        # Convert to times
        detections = [(idx / audio_sr, correlation[idx]) for idx in peaks]
        detections.sort(key=lambda x: x[1], reverse=True)
        
        # Check accuracy
        found = 0
        for known_time in known_times:
            if known_time > 600:  # Skip if beyond our test duration
                continue
            close_matches = [t for t, s in detections if abs(t - known_time) <= 10]
            if close_matches:
                found += 1
        
        accuracy = found / min(len(known_times), len([t for t in known_times if t <= 600]))
        
        print(f"Threshold {percentile:4.1f}% ({threshold:.6f}): {len(detections):2d} detections, {accuracy:.1%} accuracy")

if __name__ == "__main__":
    debug_correlation_comparison()
    test_correlation_thresholds()