"""
Extract expanded inning patterns with 1 second padding on each side,
then find the best 2-second segment within each 4-second window.
"""

import librosa
import soundfile as sf
import numpy as np
from scipy import signal
from pathlib import Path
import matplotlib.pyplot as plt

def extract_expanded_patterns():
    """
    Extract 4-second windows around each timestamp and find the best pattern within each.
    """
    print("Extracting Expanded Inning Patterns")
    print("=" * 50)
    print("Expanding to 4-second windows (±1s) to find exact pattern locations")
    
    # All 5 transitions with expanded windows
    transitions = [
        {"time_mm_ss": "2:28", "time_seconds": 148, "description": "Top 1st to Bottom 1st"},
        {"time_mm_ss": "3:19", "time_seconds": 199, "description": "Bottom 1st to Top 2nd"}, 
        {"time_mm_ss": "4:03", "time_seconds": 243, "description": "Top 2nd to Bottom 2nd"},
        {"time_mm_ss": "5:14", "time_seconds": 314, "description": "Bottom 2nd to Top 3rd"},
        {"time_mm_ss": "7:34", "time_seconds": 454, "description": "Top 3rd to Bottom 3rd"},
    ]
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    output_dir = Path("reference_sounds")
    output_dir.mkdir(exist_ok=True)
    
    expanded_dir = output_dir / "expanded_analysis"
    expanded_dir.mkdir(exist_ok=True)
    
    print(f"\nAnalyzing {len(transitions)} transitions with expanded windows...")
    
    best_segments = []
    
    for i, transition in enumerate(transitions):
        time_str = transition["time_mm_ss"]
        center_time = transition["time_seconds"]
        description = transition["description"]
        
        print(f"\n{i+1}. {time_str} - {description}")
        print(f"   Analyzing 4-second window: {center_time-1}s to {center_time+3}s")
        
        try:
            # Load 4-second window around the timestamp
            expanded_audio, sample_rate = librosa.load(
                audio_file,
                sr=22050,
                offset=max(0, center_time - 1),  # 1 second before
                duration=4.0  # Total 4 seconds
            )
            
            print(f"   Loaded: {len(expanded_audio)/sample_rate:.1f}s ({len(expanded_audio):,} samples)")
            
            # Save the full 4-second window for analysis
            expanded_filename = f"expanded_{i+1}_{time_str.replace(':', '-')}_4sec.wav"
            expanded_path = expanded_dir / expanded_filename
            sf.write(str(expanded_path), expanded_audio, sample_rate)
            
            # Analyze the 4-second window to find the loudest/most distinctive 2-second segment
            segment_length = int(2.0 * sample_rate)  # 2 seconds in samples
            
            # Method 1: Find segment with highest RMS energy
            rms_scores = []
            for start_sample in range(0, len(expanded_audio) - segment_length + 1, int(0.1 * sample_rate)):
                segment = expanded_audio[start_sample:start_sample + segment_length]
                rms = np.sqrt(np.mean(segment**2))
                rms_scores.append((start_sample, rms))
            
            # Find best RMS segment
            best_rms_start, best_rms_score = max(rms_scores, key=lambda x: x[1])
            best_rms_segment = expanded_audio[best_rms_start:best_rms_start + segment_length]
            best_rms_time_offset = best_rms_start / sample_rate
            
            # Method 2: Find segment with most distinctive spectral content
            spectral_scores = []
            for start_sample in range(0, len(expanded_audio) - segment_length + 1, int(0.1 * sample_rate)):
                segment = expanded_audio[start_sample:start_sample + segment_length]
                # Use spectral centroid as a measure of distinctiveness
                spectral_centroid = librosa.feature.spectral_centroid(y=segment, sr=sample_rate)[0]
                spectral_score = np.std(spectral_centroid)  # Higher variation = more distinctive
                spectral_scores.append((start_sample, spectral_score))
            
            best_spectral_start, best_spectral_score = max(spectral_scores, key=lambda x: x[1])
            best_spectral_segment = expanded_audio[best_spectral_start:best_spectral_start + segment_length]
            best_spectral_time_offset = best_spectral_start / sample_rate
            
            # Method 3: Find segment with highest peak amplitude
            peak_scores = []
            for start_sample in range(0, len(expanded_audio) - segment_length + 1, int(0.1 * sample_rate)):
                segment = expanded_audio[start_sample:start_sample + segment_length]
                peak = np.max(np.abs(segment))
                peak_scores.append((start_sample, peak))
            
            best_peak_start, best_peak_score = max(peak_scores, key=lambda x: x[1])
            best_peak_segment = expanded_audio[best_peak_start:best_peak_start + segment_length]
            best_peak_time_offset = best_peak_start / sample_rate
            
            print(f"   Analysis results:")
            print(f"     Best RMS: offset {best_rms_time_offset:.1f}s, score {best_rms_score:.4f}")
            print(f"     Best spectral: offset {best_spectral_time_offset:.1f}s, score {best_spectral_score:.4f}")
            print(f"     Best peak: offset {best_peak_time_offset:.1f}s, score {best_peak_score:.4f}")
            
            # Save all three candidate segments
            methods = [
                ("rms", best_rms_segment, best_rms_time_offset, best_rms_score),
                ("spectral", best_spectral_segment, best_spectral_time_offset, best_spectral_score),
                ("peak", best_peak_segment, best_peak_time_offset, best_peak_score)
            ]
            
            for method_name, segment, offset, score in methods:
                method_filename = f"method_{method_name}_{i+1}_{time_str.replace(':', '-')}.wav"
                method_path = expanded_dir / method_filename
                sf.write(str(method_path), segment, sample_rate)
                print(f"     [SAVED] {method_name}: {method_filename}")
            
            # For now, use RMS method as the default (tends to work well for game sounds)
            best_segments.append({
                'original_time': center_time,
                'time_str': time_str,
                'description': description,
                'segment': best_rms_segment,
                'offset': best_rms_time_offset,
                'actual_time': center_time - 1 + best_rms_time_offset,
                'method': 'rms',
                'score': best_rms_score
            })
            
        except Exception as e:
            print(f"   [ERROR] Failed to process {time_str}: {e}")
    
    # Build new reference pattern from the refined segments
    if best_segments:
        print(f"\n{'='*50}")
        print("BUILDING REFINED REFERENCE PATTERN")
        print(f"{'='*50}")
        
        print("Refined segment locations:")
        for seg in best_segments:
            actual_mm = int(seg['actual_time'] // 60)
            actual_ss = int(seg['actual_time'] % 60)
            offset_str = f"{seg['offset']:+.1f}s" if seg['offset'] != 1.0 else "center"
            print(f"  {seg['time_str']} -> {actual_mm:2d}:{actual_ss:02d} ({offset_str}, RMS: {seg['score']:.4f})")
        
        # Create average pattern from refined segments
        segments_only = [seg['segment'] for seg in best_segments]
        
        # Ensure all same length
        min_length = min(len(seg) for seg in segments_only)
        trimmed_segments = [seg[:min_length] for seg in segments_only]
        
        # Calculate refined average
        refined_pattern = np.mean(trimmed_segments, axis=0)
        
        # Save refined pattern
        refined_filename = output_dir / "refined_inning_transition_pattern.wav"
        sf.write(str(refined_filename), refined_pattern, 22050)
        
        print(f"\n[SAVED] Refined pattern: {refined_filename}")
        print(f"        Based on optimally-aligned segments from expanded windows")
        print(f"        Length: {len(refined_pattern):,} samples ({len(refined_pattern)/22050:.3f}s)")
        
        # Compare with previous pattern
        try:
            old_pattern, _ = librosa.load("reference_sounds/improved_inning_transition_pattern.wav", sr=22050)
            if len(old_pattern) == len(refined_pattern):
                correlation = np.corrcoef(old_pattern, refined_pattern)[0, 1]
                print(f"        Similarity to previous pattern: {correlation:.4f}")
        except:
            print("        Could not compare with previous pattern")
        
        return best_segments, refined_pattern
    
    else:
        print("No segments successfully extracted!")
        return [], None

if __name__ == "__main__":
    segments, pattern = extract_expanded_patterns()
    
    if segments:
        print(f"\n{'='*50}")
        print("SUCCESS! Refined inning patterns extracted!")
        print("The expanded analysis should have captured the 4:03 transition better.")
        print("Ready to test improved pattern matching!")
        print(f"{'='*50}")
    else:
        print("Failed to extract refined patterns")