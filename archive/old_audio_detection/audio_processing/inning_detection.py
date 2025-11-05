"""
Inning Detection Module for Mario Baseball Stats Tracking

This module helps identify and extract the specific sound that plays
at the start/end of innings in Mario Baseball games. We'll use this
as a reference pattern for automated inning detection.
"""

import librosa
import numpy as np
import soundfile as sf
from pathlib import Path
import matplotlib.pyplot as plt


class InningDetector:
    def __init__(self):
        """
        Initialize the inning detector.
        """
        self.audio_data = None
        self.sample_rate = None
        self.duration = None
        self.reference_pattern = None
        self.reference_pattern_sr = None
    
    def load_audio(self, audio_file_path, max_duration=600):
        """
        Load audio file for analysis (limit to first 10 minutes for faster processing).
        
        Args:
            audio_file_path (str): Path to the audio file
            max_duration (float): Maximum duration to load in seconds
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            print(f"Loading audio: {audio_file_path}")
            print(f"Loading first {max_duration/60:.1f} minutes for analysis...")
            
            # Load audio with duration limit and standard sample rate
            self.audio_data, self.sample_rate = librosa.load(
                audio_file_path, 
                sr=22050,  # Standard sample rate for audio analysis
                duration=max_duration
            )
            
            self.duration = len(self.audio_data) / self.sample_rate
            
            print(f"[SUCCESS] Loaded {self.duration:.1f} seconds of audio")
            print(f"Sample rate: {self.sample_rate:,} Hz")
            print(f"Total samples: {len(self.audio_data):,}")
            
            return True
            
        except Exception as e:
            print(f"Error loading audio: {str(e)}")
            return False
    
    def find_potential_inning_sounds(self, min_silence_gap=5.0, loud_threshold_percentile=85):
        """
        Find potential inning transition sounds by looking for loud moments
        separated by periods of relative silence.
        
        Args:
            min_silence_gap (float): Minimum gap of relative silence between sounds
            loud_threshold_percentile (float): Percentile threshold for "loud" sounds
            
        Returns:
            list: List of (start_time, end_time, peak_amplitude) for potential sounds
        """
        if self.audio_data is None:
            print("No audio loaded")
            return []
        
        print(f"\nSearching for potential inning sounds...")
        print(f"Looking for loud sounds separated by {min_silence_gap}s+ of silence")
        
        # Calculate amplitude envelope
        amplitude = np.abs(self.audio_data)
        
        # Smooth the amplitude for better detection
        window_size = int(0.1 * self.sample_rate)  # 100ms window
        smoothed_amplitude = np.convolve(amplitude, np.ones(window_size)/window_size, mode='same')
        
        # Set thresholds
        loud_threshold = np.percentile(smoothed_amplitude, loud_threshold_percentile)
        silence_threshold = np.percentile(smoothed_amplitude, 30)  # 30th percentile for "quiet"
        
        print(f"Loud threshold: {loud_threshold:.4f}")
        print(f"Silence threshold: {silence_threshold:.4f}")
        
        # Find loud regions
        loud_samples = smoothed_amplitude > loud_threshold
        
        # Find transitions
        transitions = np.diff(loud_samples.astype(int))
        loud_starts = np.where(transitions == 1)[0] + 1
        loud_ends = np.where(transitions == -1)[0] + 1
        
        # Handle edge cases
        if loud_samples[0]:
            loud_starts = np.concatenate([[0], loud_starts])
        if loud_samples[-1]:
            loud_ends = np.concatenate([loud_ends, [len(loud_samples)]])
        
        # Filter by silence gaps
        potential_sounds = []
        last_end_time = 0
        
        for start_idx, end_idx in zip(loud_starts, loud_ends):
            start_time = start_idx / self.sample_rate
            end_time = end_idx / self.sample_rate
            
            # Check if there's enough silence before this sound
            silence_gap = start_time - last_end_time
            if silence_gap >= min_silence_gap or len(potential_sounds) == 0:
                # Calculate peak amplitude in this region
                peak_amp = np.max(amplitude[start_idx:end_idx])
                duration = end_time - start_time
                
                # Filter out very short sounds (likely not inning transitions)
                if duration >= 0.5:  # At least 0.5 second duration
                    potential_sounds.append((start_time, end_time, peak_amp, duration))
            
            last_end_time = end_time
        
        # Sort by peak amplitude (loudest first)
        potential_sounds.sort(key=lambda x: x[2], reverse=True)
        
        print(f"\nFound {len(potential_sounds)} potential inning sounds:")
        for i, (start, end, peak, dur) in enumerate(potential_sounds[:10]):
            print(f"  {i+1}: {start:.1f}s-{end:.1f}s (duration: {dur:.1f}s, peak: {peak:.4f})")
        
        return potential_sounds
    
    def extract_audio_segment(self, start_time, end_time, padding=0.5):
        """
        Extract a segment of audio with optional padding.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds  
            padding (float): Extra time to include before/after (seconds)
            
        Returns:
            tuple: (audio_segment, actual_start_time, actual_end_time)
        """
        if self.audio_data is None:
            print("No audio loaded")
            return None, None, None
        
        # Add padding and ensure we stay within bounds
        padded_start = max(0, start_time - padding)
        padded_end = min(self.duration, end_time + padding)
        
        start_sample = int(padded_start * self.sample_rate)
        end_sample = int(padded_end * self.sample_rate)
        
        segment = self.audio_data[start_sample:end_sample]
        
        print(f"Extracted segment: {padded_start:.1f}s to {padded_end:.1f}s ({len(segment):,} samples)")
        
        return segment, padded_start, padded_end
    
    def save_audio_segment(self, audio_segment, filename, start_time=None, end_time=None):
        """
        Save an audio segment to a WAV file for manual inspection.
        
        Args:
            audio_segment (np.array): Audio data to save
            filename (str): Output filename
            start_time (float): Original start time (for filename)
            end_time (float): Original end time (for filename)
        """
        try:
            # Create reference_sounds directory if it doesn't exist
            output_dir = Path("reference_sounds")
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename with time info
            if start_time is not None and end_time is not None:
                time_info = f"_{start_time:.1f}s-{end_time:.1f}s"
                filename = f"{Path(filename).stem}{time_info}.wav"
            
            output_path = output_dir / filename
            
            # Save as WAV file
            sf.write(str(output_path), audio_segment, self.sample_rate)
            
            print(f"[SAVED] Audio segment: {output_path}")
            print(f"        Duration: {len(audio_segment)/self.sample_rate:.2f} seconds")
            print(f"        You can listen to this file to identify inning sounds!")
            
            return str(output_path)
            
        except Exception as e:
            print(f"Error saving audio segment: {str(e)}")
            return None
    
    def plot_audio_segment(self, audio_segment, title="Audio Segment"):
        """
        Plot an audio segment for visual inspection.
        """
        try:
            time_axis = np.linspace(0, len(audio_segment)/self.sample_rate, len(audio_segment))
            
            plt.figure(figsize=(12, 4))
            plt.plot(time_axis, audio_segment)
            plt.title(title)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Amplitude')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"Plotting not available: {e}")


def manual_inning_sound_extraction():
    """
    Interactive process to help identify and extract inning transition sounds.
    """
    print("=" * 60)
    print("MANUAL INNING SOUND IDENTIFICATION")
    print("=" * 60)
    print("This tool will help you find and extract the inning transition sound")
    print("that plays at the start/end of innings in Mario Baseball.")
    print()
    
    # Load the audio
    detector = InningDetector()
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    
    if not detector.load_audio(audio_file, max_duration=600):  # First 10 minutes
        print("Failed to load audio file")
        return
    
    # Find potential inning sounds
    potential_sounds = detector.find_potential_inning_sounds(
        min_silence_gap=3.0,  # Inning transitions usually have silence before/after
        loud_threshold_percentile=80  # Look for moderately loud sounds
    )
    
    if not potential_sounds:
        print("No potential inning sounds found")
        return
    
    print(f"\n{'='*60}")
    print("EXTRACTING TOP CANDIDATES FOR MANUAL REVIEW")
    print(f"{'='*60}")
    
    # Extract and save the top 5 candidates
    candidates_to_save = min(5, len(potential_sounds))
    
    for i in range(candidates_to_save):
        start_time, end_time, peak_amp, duration = potential_sounds[i]
        
        print(f"\nCandidate {i+1}: {start_time:.1f}s-{end_time:.1f}s")
        
        # Extract the segment with some padding
        segment, actual_start, actual_end = detector.extract_audio_segment(
            start_time, end_time, padding=1.0  # 1 second padding
        )
        
        if segment is not None:
            # Save for manual review
            filename = f"candidate_{i+1}_inning_sound"
            saved_path = detector.save_audio_segment(
                segment, filename, actual_start, actual_end
            )
    
    print(f"\n{'='*60}")
    print("NEXT STEPS FOR MANUAL REVIEW:")
    print(f"{'='*60}")
    print("1. Check the 'reference_sounds' folder")
    print("2. Listen to each candidate WAV file")
    print("3. Identify which one is the inning transition sound")
    print("4. The inning sound typically:")
    print("   - Plays at the start of each inning")
    print("   - Is a distinctive game sound effect")
    print("   - Is NOT crowd noise, commentary, or music") 
    print("   - Happens consistently throughout the game")
    print()
    print("Once you identify the correct sound, we'll use it as our")
    print("reference pattern for automated inning detection!")


if __name__ == "__main__":
    manual_inning_sound_extraction()