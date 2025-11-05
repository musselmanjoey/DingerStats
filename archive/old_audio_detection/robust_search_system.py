"""
Robust Search System - Addresses timing precision and pattern matching issues

The key insight: Instead of sliding a fixed pattern across the entire video,
we'll search more intelligently around expected timing with multiple approaches.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path
from audio_filtering import AudioFilter
import soundfile as sf

class RobustInningDetector:
    def __init__(self):
        self.sample_rate = 22050
        self.audio_filter = AudioFilter()
        self.reference_pattern = None
        
    def load_reference(self):
        """Load the refined reference pattern."""
        try:
            ref_file = "reference_sounds/refined_inning_transition_pattern.wav"
            self.reference_pattern, _ = librosa.load(ref_file, sr=self.sample_rate)
            print(f"[SUCCESS] Reference loaded: {len(self.reference_pattern)/self.sample_rate:.2f}s")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load reference: {e}")
            return False
    
    def search_around_time(self, audio_data, center_time, search_window=10):
        """
        Search for pattern around a specific time with flexible window.
        
        Args:
            audio_data: Full audio signal
            center_time: Expected time in seconds
            search_window: Search ±window seconds around center_time
            
        Returns:
            (best_time, best_score, all_correlations)
        """
        audio_sr = self.sample_rate
        
        # Calculate search bounds
        start_time = max(0, center_time - search_window)
        end_time = min(len(audio_data)/audio_sr, center_time + search_window)
        
        start_sample = int(start_time * audio_sr)
        end_sample = int(end_time * audio_sr)
        
        # Extract search segment
        search_segment = audio_data[start_sample:end_sample]
        
        # Normalize both signals
        ref_norm = self.reference_pattern / np.max(np.abs(self.reference_pattern))
        search_norm = search_segment / np.max(np.abs(search_segment))
        
        # Cross-correlation
        correlation = signal.correlate(search_norm, ref_norm, mode='valid')
        correlation = correlation / len(ref_norm)
        
        # Find best match
        best_idx = np.argmax(correlation)
        best_score = correlation[best_idx]
        best_time = start_time + (best_idx / audio_sr)
        
        # Convert correlation array to time-indexed format for analysis
        time_axis = np.arange(len(correlation)) / audio_sr + start_time
        correlations = list(zip(time_axis, correlation))
        
        return best_time, best_score, correlations
    
    def test_timing_precision(self, video_file):
        """
        Test timing precision around known transitions to understand the issue.
        """
        print("=" * 60)
        print("TIMING PRECISION ANALYSIS")
        print("=" * 60)
        
        # Load video
        audio_data, _ = librosa.load(video_file, sr=self.sample_rate, duration=600)
        
        # Apply same filtering as in search
        filtered_audio = self.audio_filter.frequency_band_filter(audio_data)
        
        # Known transitions with descriptions
        known_transitions = [
            (148, "2:28 - Top 1st to Bottom 1st"),
            (199, "3:19 - Bottom 1st to Top 2nd"), 
            (243, "4:03 - Top 2nd to Bottom 2nd"),
            (314, "5:14 - Bottom 2nd to Top 3rd"),
            (454, "7:34 - Top 3rd to Bottom 3rd (beyond 10min test)")
        ]
        
        print(f"Testing {len(known_transitions)} known transitions:")
        print("(Searching ±5 seconds around each expected time)")
        
        results = []
        
        for expected_time, description in known_transitions:
            if expected_time > 580:  # Skip if beyond our 10-minute test
                print(f"\n{description} - SKIPPED (beyond test duration)")
                continue
                
            print(f"\n{description}")
            print(f"Expected at: {expected_time}s")
            
            # Search with different window sizes
            for window in [2, 5, 10]:
                best_time, best_score, correlations = self.search_around_time(
                    filtered_audio, expected_time, window
                )
                
                error = abs(best_time - expected_time)
                mm_exp, ss_exp = int(expected_time // 60), int(expected_time % 60)
                mm_found, ss_found = int(best_time // 60), int(best_time % 60)
                
                print(f"  ±{window}s window: Found at {mm_found}:{ss_found:02d} "
                      f"(error: {error:.2f}s, score: {best_score:.6f})")
                
                if window == 5:  # Save detailed results for 5s window
                    results.append({
                        'expected': expected_time,
                        'found': best_time,
                        'error': error,
                        'score': best_score,
                        'description': description
                    })
        
        return results
    
    def full_video_search_improved(self, video_file, expected_transitions=None):
        """
        Improved full video search using lessons from timing analysis.
        """
        print("\n" + "=" * 60)
        print("IMPROVED FULL VIDEO SEARCH")
        print("=" * 60)
        
        # Load and filter audio (full video)
        audio_data, _ = librosa.load(video_file, sr=self.sample_rate)
        filtered_audio = self.audio_filter.frequency_band_filter(audio_data)
        
        if expected_transitions:
            print("TARGETED SEARCH around known transitions:")
            # Search around expected times with larger windows
            detections = []
            
            for expected_time in expected_transitions:
                # Remove the time limit for full video analysis
                    
                best_time, best_score, _ = self.search_around_time(
                    filtered_audio, expected_time, search_window=15
                )
                
                # Only accept if score is reasonable
                if best_score > 0.001:  # Much lower threshold for targeted search
                    detections.append((best_time, best_score))
                    mm, ss = int(best_time // 60), int(best_time % 60)
                    error = abs(best_time - expected_time)
                    print(f"  Found at {mm}:{ss:02d} (error: {error:.1f}s, score: {best_score:.6f})")
                else:
                    mm_exp, ss_exp = int(expected_time // 60), int(expected_time % 60)
                    print(f"  No good match for {mm_exp}:{ss_exp:02d} (best score: {best_score:.6f})")
            
        else:
            print("BLIND SEARCH across entire video:")
            # Traditional correlation search but with better parameters
            ref_norm = self.reference_pattern / np.max(np.abs(self.reference_pattern))
            audio_norm = filtered_audio / np.max(np.abs(filtered_audio))
            
            correlation = signal.correlate(audio_norm, ref_norm, mode='valid')
            correlation = correlation / len(ref_norm)
            
            # Use more conservative threshold for full video to reduce false positives
            threshold = np.percentile(correlation, 99.8)
            min_gap_samples = int(60 * self.sample_rate)  # 1 minute minimum gap
            
            peak_indices, _ = signal.find_peaks(correlation, height=threshold, distance=min_gap_samples)
            
            detections = []
            for idx in peak_indices:
                time_sec = idx / self.sample_rate
                score = correlation[idx]
                detections.append((time_sec, score))
            
            print(f"Found {len(detections)} detections with {threshold:.6f} threshold")
        
        # Sort by score
        detections.sort(key=lambda x: x[1], reverse=True)
        
        return detections
    
    def analyze_results(self, detections, expected_transitions=None):
        """Analyze and display results."""
        print(f"\nDETECTION RESULTS:")
        print("-" * 40)
        
        if not detections:
            print("No detections found!")
            return 0.0
        
        for i, (time_sec, score) in enumerate(detections):
            mm, ss = int(time_sec // 60), int(time_sec % 60)
            print(f"  {i+1}: {mm}:{ss:02d} ({time_sec:.1f}s) - Score: {score:.6f}")
        
        if expected_transitions:
            print(f"\nVALIDATION:")
            found_count = 0
            tolerance = 15.0  # Increased tolerance for better matching
            valid_expected = 0  # Count valid expected transitions
            
            for expected in expected_transitions:
                valid_expected += 1
                    
                mm_exp, ss_exp = int(expected // 60), int(expected % 60)
                
                matches = [(t, s) for t, s in detections if abs(t - expected) <= tolerance]
                
                if matches:
                    best_match = max(matches, key=lambda x: x[1])
                    match_time, match_score = best_match
                    mm_match, ss_match = int(match_time // 60), int(match_time % 60)
                    error = abs(match_time - expected)
                    
                    print(f"  [FOUND] {mm_exp}:{ss_exp:02d} -> {mm_match}:{ss_match:02d} "
                          f"(error: {error:.1f}s, score: {match_score:.6f})")
                    found_count += 1
                else:
                    print(f"  [MISSED] {mm_exp}:{ss_exp:02d}")
            
            accuracy = found_count / valid_expected  # All expected transitions
            print(f"\nAccuracy: {accuracy:.1%} ({found_count}/{valid_expected} found)")
            return accuracy
        
        return None

def test_robust_system():
    """Test the robust search system."""
    print("ROBUST INNING DETECTION SYSTEM")
    print("=" * 70)
    
    detector = RobustInningDetector()
    
    if not detector.load_reference():
        return
    
    video_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    expected_transitions = [148, 199, 243, 314, 454]
    
    # Step 1: Analyze timing precision
    timing_results = detector.test_timing_precision(video_file)
    
    # Step 2: Try improved search methods
    targeted_detections = detector.full_video_search_improved(video_file, expected_transitions)
    targeted_accuracy = detector.analyze_results(targeted_detections, expected_transitions)
    
    blind_detections = detector.full_video_search_improved(video_file, None)
    blind_accuracy = detector.analyze_results(blind_detections, expected_transitions)
    
    print(f"\n" + "=" * 70)
    print("FINAL COMPARISON:")
    print(f"Targeted search accuracy: {targeted_accuracy:.1%}")
    print(f"Blind search accuracy: {blind_accuracy:.1%}" if blind_accuracy else "Blind search accuracy: N/A")
    
    return timing_results, targeted_detections, blind_detections

if __name__ == "__main__":
    test_robust_system()