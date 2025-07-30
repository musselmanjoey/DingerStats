"""
Final Pattern Matching System with Official Reference and Spectral Filtering

This combines the official "Next Inning" audio with spectral filtering
to achieve accurate inning transition detection in Dinger City videos.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path
from audio_filtering import AudioFilter

class FinalInningDetector:
    def __init__(self):
        """
        Initialize the final inning detection system.
        """
        self.sample_rate = 22050
        self.audio_filter = AudioFilter()
        self.reference_pattern = None
        self.reference_sr = None
        
    def load_official_reference(self):
        """
        Load the official "Next Inning" reference pattern.
        """
        try:
            reference_file = "reference_sounds/official_inning_transition_pattern.wav"
            self.reference_pattern, self.reference_sr = librosa.load(reference_file, sr=self.sample_rate)
            
            print(f"[SUCCESS] Official reference loaded:")
            print(f"  Duration: {len(self.reference_pattern)/self.reference_sr:.2f}s")
            print(f"  RMS: {np.sqrt(np.mean(self.reference_pattern**2)):.4f}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load official reference: {e}")
            return False
    
    def detect_innings_with_filtering(self, video_file, max_duration=1800):
        """
        Detect inning transitions using official reference and spectral filtering.
        
        Args:
            video_file (str): Path to video file
            max_duration (float): Maximum duration to analyze in seconds
            
        Returns:
            list: Detected inning transitions with timestamps and scores
        """
        print(f"\nAnalyzing: {Path(video_file).name}")
        print("-" * 50)
        
        # Load video audio
        try:
            print("Loading video audio...")
            audio_data, audio_sr = librosa.load(video_file, sr=self.sample_rate, duration=max_duration)
            duration_minutes = len(audio_data) / audio_sr / 60
            print(f"Loaded: {duration_minutes:.1f} minutes")
            
        except Exception as e:
            print(f"[ERROR] Failed to load audio: {e}")
            return []
        
        # Apply spectral filtering (best approach from testing)
        print("Applying spectral filtering to remove commentary...")
        filter_config = {
            "spectral_subtraction": True,
            "frequency_band": False, 
            "compression": False,
            "noise_gate": False
        }
        
        filtered_audio = self.audio_filter.apply_combined_filter(audio_data, filter_config)
        
        # Normalize both signals for correlation
        print("Computing cross-correlation with official pattern...")
        ref_normalized = self.reference_pattern / np.max(np.abs(self.reference_pattern))
        audio_normalized = filtered_audio / np.max(np.abs(filtered_audio))
        
        # Cross-correlation
        correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
        correlation = correlation / len(ref_normalized)
        
        print(f"Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
        
        # Adaptive threshold based on correlation statistics
        # Use a more conservative threshold since we have clean reference
        correlation_mean = np.mean(correlation)
        correlation_std = np.std(correlation)
        threshold = correlation_mean + (3 * correlation_std)  # 3 standard deviations above mean
        
        # Alternative: Use percentile-based threshold
        percentile_threshold = np.percentile(correlation, 99.8)  # Very selective
        
        # Use the higher of the two thresholds for maximum selectivity
        final_threshold = max(threshold, percentile_threshold)
        
        print(f"Adaptive threshold: {threshold:.6f}")
        print(f"Percentile threshold: {percentile_threshold:.6f}")
        print(f"Final threshold: {final_threshold:.6f}")
        
        # Find peaks with realistic spacing (minimum 90 seconds between innings)
        min_gap_samples = int(90 * audio_sr)  # 1.5 minutes minimum
        
        peak_indices, properties = signal.find_peaks(
            correlation,
            height=final_threshold,
            distance=min_gap_samples
        )
        
        # Convert to timestamps and scores
        detections = []
        for idx in peak_indices:
            time_seconds = idx / audio_sr
            correlation_score = correlation[idx]
            detections.append((time_seconds, correlation_score))
        
        # Sort by correlation score (highest first)
        detections.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Found {len(detections)} potential inning transitions")
        
        return detections
    
    def analyze_detection_results(self, detections, video_name, known_transitions=None):
        """
        Analyze and display detection results.
        """
        print(f"\nDETECTION RESULTS - {video_name}")
        print("=" * 60)
        
        if not detections:
            print("No inning transitions detected!")
            if known_transitions:
                print("This suggests:")
                print("- Filtering may be too aggressive")
                print("- Threshold may be too high") 
                print("- Video may have different audio characteristics")
            return
        
        print(f"Detected {len(detections)} inning transitions:")
        
        for i, (time_sec, score) in enumerate(detections):
            mm = int(time_sec // 60)
            ss = int(time_sec % 60)
            print(f"  {i+1:2d}: {mm:2d}:{ss:02d} ({time_sec:6.1f}s) - Score: {score:.6f}")
        
        # Analyze timing patterns
        if len(detections) >= 2:
            times = [time for time, score in detections]
            gaps = [times[i+1] - times[i] for i in range(len(times)-1)]
            avg_gap = np.mean(gaps)
            
            print(f"\nTiming Analysis:")
            print(f"  Average gap: {avg_gap:.1f}s ({avg_gap/60:.1f} minutes)")
            print(f"  Gap range: {min(gaps):.1f}s to {max(gaps):.1f}s")
            
            # Assess if timing makes sense for baseball
            if 120 <= avg_gap <= 400:  # 2-7 minutes per inning
                print(f"  [REALISTIC] Gap timing consistent with baseball innings")
            else:
                print(f"  [QUESTIONABLE] Gap timing unusual for baseball")
        
        # Compare against known transitions if provided
        if known_transitions:
            print(f"\nValidation against known transitions:")
            tolerance = 10.0  # 10 second tolerance
            found_count = 0
            
            for known_time in known_transitions:
                known_mm = int(known_time // 60)
                known_ss = int(known_time % 60)
                
                # Find closest detection
                closest_detections = [
                    (time, score) for time, score in detections
                    if abs(time - known_time) <= tolerance
                ]
                
                if closest_detections:
                    best_match = max(closest_detections, key=lambda x: x[1])
                    match_time, match_score = best_match
                    match_mm = int(match_time // 60)
                    match_ss = int(match_time % 60)
                    error = abs(match_time - known_time)
                    
                    print(f"  [FOUND] {known_mm:2d}:{known_ss:02d} -> {match_mm:2d}:{match_ss:02d} (error: {error:.1f}s, score: {match_score:.6f})")
                    found_count += 1
                else:
                    print(f"  [MISSED] {known_mm:2d}:{known_ss:02d} -> No detection within {tolerance}s")
            
            accuracy = found_count / len(known_transitions) if known_transitions else 0
            print(f"\nAccuracy: {accuracy:.1%} ({found_count}/{len(known_transitions)} found)")
            
            return accuracy
        
        return None

def test_final_system():
    """
    Test the final pattern matching system on both videos.
    """
    print("=" * 70)
    print("FINAL INNING DETECTION SYSTEM TEST")
    print("=" * 70)
    print("Using official 'Next Inning' reference + spectral filtering")
    
    detector = FinalInningDetector()
    
    # Load official reference
    if not detector.load_official_reference():
        print("Cannot proceed without official reference pattern")
        return
    
    # Test videos with known results
    test_videos = [
        {
            "name": "Original Video (Training Data)",
            "file": "temp_audio/The CRAZIEST hit in Mario Baseball.webm",
            "known_transitions": [148, 199, 243, 314, 454],  # Our known 5 transitions
            "expected_accuracy": "100%"
        },
        {
            "name": "New Video (Monty Mole)",
            "file": "temp_audio_new/Is Monty Mole enough to make the playoffs？？.webm", 
            "known_transitions": None,  # Unknown - we'll see what it finds
            "expected_accuracy": "Unknown"
        }
    ]
    
    results = {}
    
    for video in test_videos:
        print(f"\n{'='*70}")
        print(f"TESTING: {video['name']}")
        print(f"Expected: {video['expected_accuracy']}")
        print(f"{'='*70}")
        
        # Detect inning transitions
        detections = detector.detect_innings_with_filtering(video['file'])
        
        # Analyze results
        accuracy = detector.analyze_detection_results(
            detections, 
            video['name'], 
            video['known_transitions']
        )
        
        results[video['name']] = {
            'detections': len(detections),
            'accuracy': accuracy
        }
    
    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SYSTEM PERFORMANCE SUMMARY")
    print(f"{'='*70}")
    
    for video_name, result in results.items():
        accuracy_str = f"{result['accuracy']:.1%}" if result['accuracy'] is not None else "N/A"
        print(f"{video_name}:")
        print(f"  Detections: {result['detections']}")
        print(f"  Accuracy: {accuracy_str}")
    
    print(f"\nSystem Status:")
    original_accuracy = results.get("Original Video (Training Data)", {}).get('accuracy', 0)
    
    if original_accuracy and original_accuracy >= 0.8:
        print("✅ EXCELLENT - System working well on known data")
        print("🎯 Ready for production use on Mario Baseball videos")
    elif original_accuracy and original_accuracy >= 0.6:
        print("✅ GOOD - System shows promise, may need minor tuning")
    else:
        print("⚠️ NEEDS WORK - System not detecting known transitions accurately")
    
    return results

if __name__ == "__main__":
    test_final_system()