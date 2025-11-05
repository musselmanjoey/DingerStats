"""
Pattern Matching Module for Automated Inning Detection

This module uses scipy.signal.correlate() to find all instances of the
inning transition sound pattern throughout the full Mario Baseball video.
"""

import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path
import matplotlib.pyplot as plt


class InningPatternMatcher:
    def __init__(self):
        """
        Initialize the pattern matcher.
        """
        self.reference_pattern = None
        self.reference_sr = None
        self.audio_data = None
        self.audio_sr = None
        self.correlation_scores = None
        
    def load_reference_pattern(self, pattern_file="reference_sounds/inning_transition_average_pattern.wav"):
        """
        Load the reference inning transition pattern.
        
        Args:
            pattern_file (str): Path to the reference pattern WAV file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            print(f"Loading reference pattern: {pattern_file}")
            
            self.reference_pattern, self.reference_sr = librosa.load(pattern_file, sr=22050)
            
            print(f"[SUCCESS] Reference pattern loaded")
            print(f"  Duration: {len(self.reference_pattern)/self.reference_sr:.3f} seconds")
            print(f"  Sample rate: {self.reference_sr:,} Hz")
            print(f"  Samples: {len(self.reference_pattern):,}")
            print(f"  Peak amplitude: {np.max(np.abs(self.reference_pattern)):.4f}")
            
            return True
            
        except Exception as e:
            print(f"Error loading reference pattern: {str(e)}")
            return False
    
    def load_full_audio(self, audio_file, max_duration=None):
        """
        Load the full audio file for pattern matching.
        
        Args:
            audio_file (str): Path to the audio file
            max_duration (float): Maximum duration to load (None for full file)
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            print(f"Loading full audio: {audio_file}")
            
            if max_duration:
                print(f"Loading first {max_duration/60:.1f} minutes...")
                self.audio_data, self.audio_sr = librosa.load(
                    audio_file, sr=22050, duration=max_duration
                )
            else:
                print("Loading full audio file (this may take a few minutes)...")
                self.audio_data, self.audio_sr = librosa.load(audio_file, sr=22050)
            
            duration = len(self.audio_data) / self.audio_sr
            print(f"[SUCCESS] Audio loaded")
            print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"  Sample rate: {self.audio_sr:,} Hz")
            print(f"  Total samples: {len(self.audio_data):,}")
            
            return True
            
        except Exception as e:
            print(f"Error loading audio: {str(e)}")
            return False
    
    def find_pattern_matches(self, correlation_threshold=0.3, min_time_gap=30.0):
        """
        Find all instances of the reference pattern in the audio using correlation.
        
        Args:
            correlation_threshold (float): Minimum correlation score to consider a match
            min_time_gap (float): Minimum time gap between matches (seconds)
            
        Returns:
            list: List of (time, correlation_score) tuples for detected matches
        """
        if self.reference_pattern is None or self.audio_data is None:
            print("Error: Reference pattern and audio must be loaded first")
            return []
        
        print(f"\nSearching for inning transition patterns...")
        print(f"Correlation threshold: {correlation_threshold}")
        print(f"Minimum time gap: {min_time_gap} seconds")
        
        # Normalize both signals to improve correlation accuracy
        ref_normalized = self.reference_pattern / np.max(np.abs(self.reference_pattern))
        audio_normalized = self.audio_data / np.max(np.abs(self.audio_data))
        
        print("Computing cross-correlation (this may take a moment)...")
        
        # Compute cross-correlation using scipy
        correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
        
        # Normalize correlation scores to 0-1 range
        correlation = correlation / len(ref_normalized)
        
        print(f"Correlation computed: {len(correlation):,} values")
        print(f"Max correlation: {np.max(correlation):.4f}")
        print(f"Mean correlation: {np.mean(correlation):.4f}")
        
        # Find peaks above threshold
        peak_indices, properties = signal.find_peaks(
            correlation, 
            height=correlation_threshold,
            distance=int(min_time_gap * self.audio_sr)  # Convert time gap to samples
        )
        
        print(f"Found {len(peak_indices)} potential matches above threshold")
        
        # Convert peak indices to time and get correlation scores
        matches = []
        for idx in peak_indices:
            time_seconds = idx / self.audio_sr
            correlation_score = correlation[idx]
            matches.append((time_seconds, correlation_score))
        
        # Sort by correlation score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Store for analysis
        self.correlation_scores = correlation
        
        return matches
    
    def analyze_matches(self, matches, known_times=[148, 243, 454]):
        """
        Analyze the detected matches against known inning transition times.
        
        Args:
            matches (list): List of (time, score) tuples from find_pattern_matches
            known_times (list): Known inning transition times in seconds for validation
            
        Returns:
            dict: Analysis results with accuracy metrics
        """
        print(f"\n{'='*60}")
        print("PATTERN MATCHING ANALYSIS")
        print(f"{'='*60}")
        
        if not matches:
            print("No matches found!")
            return {"accuracy": 0, "precision": 0, "recall": 0}
        
        print(f"Total matches found: {len(matches)}")
        print(f"Known inning transitions: {len(known_times)}")
        
        print(f"\nTOP MATCHES:")
        for i, (time, score) in enumerate(matches[:10]):
            minutes = int(time // 60)
            seconds = int(time % 60)
            print(f"  {i+1}: {minutes:2d}:{seconds:02d} ({time:6.1f}s) - Score: {score:.4f}")
        
        # Check accuracy against known times (tolerance of ±3 seconds)
        tolerance = 3.0
        true_positives = 0
        detected_known = []
        
        print(f"\nVALIDATION AGAINST KNOWN TIMES (±{tolerance}s tolerance):")
        
        for known_time in known_times:
            known_minutes = int(known_time // 60)
            known_seconds = int(known_time % 60)
            
            # Find if any match is close to this known time
            close_matches = [
                (time, score) for time, score in matches 
                if abs(time - known_time) <= tolerance
            ]
            
            if close_matches:
                best_match = max(close_matches, key=lambda x: x[1])
                match_time, match_score = best_match
                match_minutes = int(match_time // 60)
                match_seconds = int(match_time % 60)
                error = abs(match_time - known_time)
                
                print(f"  Known: {known_minutes:2d}:{known_seconds:02d} -> Detected: {match_minutes:2d}:{match_seconds:02d} (error: {error:.1f}s, score: {match_score:.4f}) ✓")
                true_positives += 1
                detected_known.append(known_time)
            else:
                print(f"  Known: {known_minutes:2d}:{known_seconds:02d} -> NOT DETECTED ✗")
        
        # Calculate metrics
        precision = true_positives / len(matches) if matches else 0
        recall = true_positives / len(known_times) if known_times else 0
        accuracy = true_positives / len(known_times) if known_times else 0
        
        print(f"\nPERFORMANCE METRICS:")
        print(f"  True Positives: {true_positives}")
        print(f"  Total Detected: {len(matches)}")
        print(f"  Total Known: {len(known_times)}")
        print(f"  Accuracy: {accuracy:.2%} ({true_positives}/{len(known_times)} known transitions detected)")
        print(f"  Precision: {precision:.2%} ({true_positives}/{len(matches)} detections were correct)")
        print(f"  Recall: {recall:.2%} (same as accuracy for this case)")
        
        return {
            "total_matches": len(matches),
            "true_positives": true_positives,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "matches": matches
        }
    
    def plot_correlation_results(self, matches, known_times=[148, 243, 454], save_plot=True):
        """
        Plot the correlation results showing detected matches and known times.
        """
        if self.correlation_scores is None:
            print("No correlation data to plot")
            return
        
        try:
            # Create time axis for correlation
            time_axis = np.arange(len(self.correlation_scores)) / self.audio_sr
            
            plt.figure(figsize=(15, 8))
            
            # Plot correlation scores
            plt.subplot(2, 1, 1)
            plt.plot(time_axis, self.correlation_scores, alpha=0.7, color='blue', linewidth=0.5)
            plt.title('Cross-Correlation Scores Over Time')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Correlation Score')
            plt.grid(True, alpha=0.3)
            
            # Mark detected matches
            match_times = [time for time, score in matches]
            match_scores = [score for time, score in matches]
            plt.scatter(match_times, match_scores, color='red', s=100, alpha=0.8, 
                       label=f'Detected Matches ({len(matches)})', zorder=5)
            
            # Mark known times
            for known_time in known_times:
                plt.axvline(x=known_time, color='green', linestyle='--', alpha=0.7, linewidth=2)
            
            plt.legend()
            
            # Plot zoomed view of first 10 minutes
            plt.subplot(2, 1, 2)
            zoom_end = min(600, len(time_axis))  # First 10 minutes or end of audio
            plt.plot(time_axis[:zoom_end], self.correlation_scores[:zoom_end], 
                    alpha=0.7, color='blue', linewidth=1)
            plt.title('Cross-Correlation Scores - First 10 Minutes (Zoomed)')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Correlation Score')
            plt.grid(True, alpha=0.3)
            
            # Mark matches in zoom view
            zoom_matches = [(t, s) for t, s in matches if t <= 600]
            if zoom_matches:
                zoom_match_times = [time for time, score in zoom_matches]
                zoom_match_scores = [score for time, score in zoom_matches]
                plt.scatter(zoom_match_times, zoom_match_scores, color='red', s=100, 
                           alpha=0.8, zorder=5)
            
            # Mark known times in zoom view
            for known_time in known_times:
                if known_time <= 600:
                    plt.axvline(x=known_time, color='green', linestyle='--', alpha=0.7, linewidth=2)
            
            plt.tight_layout()
            
            if save_plot:
                plot_file = "correlation_analysis.png"
                plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                print(f"[SAVED] Correlation plot: {plot_file}")
            
            plt.show()
            
        except Exception as e:
            print(f"Plotting error: {e}")


def run_automated_inning_detection():
    """
    Main function to run the complete automated inning detection system.
    """
    print("=" * 70)
    print("AUTOMATED INNING DETECTION SYSTEM")
    print("=" * 70)
    print("Using pattern matching to find all inning transitions in the video")
    
    # Initialize matcher
    matcher = InningPatternMatcher()
    
    # Load reference pattern
    if not matcher.load_reference_pattern():
        print("Failed to load reference pattern")
        return
    
    # Load audio (limit to first 15 minutes for testing)
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    if not matcher.load_full_audio(audio_file, max_duration=900):  # 15 minutes
        print("Failed to load audio")
        return
    
    # Find pattern matches
    matches = matcher.find_pattern_matches(
        correlation_threshold=0.2,  # Lower threshold to catch more potential matches
        min_time_gap=30.0  # Minimum 30 seconds between innings
    )
    
    # Analyze results against known times
    known_transitions = [148, 243, 454]  # From manual identification
    results = matcher.analyze_matches(matches, known_transitions)
    
    # Plot results
    print(f"\nGenerating correlation analysis plot...")
    matcher.plot_correlation_results(matches, known_transitions)
    
    # Summary
    print(f"\n{'='*70}")
    print("INNING DETECTION SUMMARY")
    print(f"{'='*70}")
    
    if results["accuracy"] >= 0.8:
        print("[SUCCESS] High accuracy inning detection achieved!")
    elif results["accuracy"] >= 0.5:
        print("[PARTIAL] Moderate accuracy - may need threshold tuning")
    else:
        print("[NEEDS WORK] Low accuracy - requires algorithm improvement")
    
    print(f"Detected {results['true_positives']}/{len(known_transitions)} known inning transitions")
    print("Ready to process full-length videos!")
    
    return results


if __name__ == "__main__":
    run_automated_inning_detection()