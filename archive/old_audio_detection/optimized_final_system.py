"""
Optimized Final Pattern Matching System

Based on debug analysis showing old refined pattern + frequency filtering 
achieves much better correlation than official audio (0.011661 vs 0.000606).
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path
from audio_filtering import AudioFilter

class OptimizedInningDetector:
    def __init__(self):
        """
        Initialize the optimized inning detection system.
        """
        self.sample_rate = 22050
        self.audio_filter = AudioFilter()
        self.reference_pattern = None
        self.reference_sr = None
        
    def load_refined_reference(self):
        """
        Load the refined reference pattern extracted from video context.
        """
        try:
            reference_file = "reference_sounds/refined_inning_transition_pattern.wav"
            self.reference_pattern, self.reference_sr = librosa.load(reference_file, sr=self.sample_rate)
            
            print(f"[SUCCESS] Refined reference loaded:")
            print(f"  Duration: {len(self.reference_pattern)/self.reference_sr:.2f}s")
            print(f"  RMS: {np.sqrt(np.mean(self.reference_pattern**2)):.4f}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load refined reference: {e}")
            return False
    
    def detect_innings_optimized(self, video_file, max_duration=1800):
        """
        Detect inning transitions using refined pattern and frequency filtering.
        
        Args:
            video_file (str): Path to video file
            max_duration (float): Maximum duration to analyze in seconds
            
        Returns:
            list: Detected inning transitions with timestamps and scores
        """
        print(f"\nAnalyzing: {Path(video_file).name.encode('ascii', 'replace').decode('ascii')}")
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
        
        # Apply frequency filtering (best approach from debug analysis)
        print("Applying frequency band filtering...")
        filtered_audio = self.audio_filter.frequency_band_filter(audio_data)
        
        # Normalize both signals for correlation
        print("Computing cross-correlation with refined pattern...")
        ref_normalized = self.reference_pattern / np.max(np.abs(self.reference_pattern))
        audio_normalized = filtered_audio / np.max(np.abs(filtered_audio))
        
        # Cross-correlation
        correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
        correlation = correlation / len(ref_normalized)
        
        print(f"Correlation range: {np.min(correlation):.6f} to {np.max(correlation):.6f}")
        
        # Use optimized threshold based on actual correlation range
        # Current max is 0.003190, we detected 2/5 at 80% threshold
        # Lower threshold to catch more transitions
        percentile_threshold = np.percentile(correlation, 98.5)  # Less aggressive
        
        # Use adaptive absolute threshold based on current correlation range
        correlation_max = np.max(correlation)
        absolute_threshold = correlation_max * 0.6  # Lower to 60% of maximum correlation
        
        # Use the higher of the two for selectivity
        final_threshold = max(percentile_threshold, absolute_threshold)
        
        print(f"Percentile threshold (98.5%): {percentile_threshold:.6f}")
        print(f"Absolute threshold: {absolute_threshold:.6f}")
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
            return 0.0
        
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

def test_optimized_system():
    """
    Test the optimized pattern matching system on both videos.
    """
    print("=" * 70)
    print("OPTIMIZED INNING DETECTION SYSTEM TEST")
    print("=" * 70)
    print("Using refined pattern + frequency filtering (best from debug)")
    
    detector = OptimizedInningDetector()
    
    # Load refined reference
    if not detector.load_refined_reference():
        print("Cannot proceed without refined reference pattern")
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
        detections = detector.detect_innings_optimized(video['file'])
        
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
    print("OPTIMIZED SYSTEM PERFORMANCE SUMMARY")
    print(f"{'='*70}")
    
    for video_name, result in results.items():
        accuracy_str = f"{result['accuracy']:.1%}" if result['accuracy'] is not None else "N/A"
        print(f"{video_name}:")
        print(f"  Detections: {result['detections']}")
        print(f"  Accuracy: {accuracy_str}")
    
    print(f"\nSystem Status:")
    original_accuracy = results.get("Original Video (Training Data)", {}).get('accuracy', 0)
    
    if original_accuracy and original_accuracy >= 0.8:
        print("[SUCCESS] EXCELLENT - System working well on known data")
        print("[READY] System ready for production use on Mario Baseball videos")
    elif original_accuracy and original_accuracy >= 0.6:
        print("[GOOD] System shows promise, may need minor tuning")
    else:
        print("[NEEDS WORK] System not detecting known transitions accurately")
    
    return results

if __name__ == "__main__":
    test_optimized_system()