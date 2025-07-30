"""
Audio Loading and Analysis Module for Mario Baseball Stats Tracking

This module uses librosa to load and analyze audio files, providing
basic audio information and visualization tools to understand the 
audio data structure for pattern matching.
"""

import librosa
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


class AudioAnalyzer:
    def __init__(self):
        """
        Initialize the audio analyzer.
        """
        self.audio_data = None
        self.sample_rate = None
        self.duration = None
        self.audio_file_path = None
    
    def load_audio(self, audio_file_path):
        """
        Load an audio file using librosa.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            print(f"Loading audio file: {audio_file_path}")
            
            # Load audio file - librosa automatically converts to mono and resamples
            # sr=None preserves original sample rate
            self.audio_data, self.sample_rate = librosa.load(audio_file_path, sr=None)
            self.audio_file_path = audio_file_path
            self.duration = len(self.audio_data) / self.sample_rate
            
            print(f"[SUCCESS] Audio loaded successfully!")
            self.show_audio_info()
            return True
            
        except Exception as e:
            print(f"Error loading audio: {str(e)}")
            return False
    
    def show_audio_info(self):
        """
        Display basic information about the loaded audio.
        """
        if self.audio_data is None:
            print("No audio data loaded")
            return
        
        print("\n" + "="*50)
        print("AUDIO FILE INFORMATION")
        print("="*50)
        print(f"File: {Path(self.audio_file_path).name}")
        print(f"Duration: {self.duration:.2f} seconds ({self.duration/60:.2f} minutes)")
        print(f"Sample Rate: {self.sample_rate:,} Hz")
        print(f"Total Samples: {len(self.audio_data):,}")
        print(f"Audio Shape: {self.audio_data.shape}")
        print(f"Audio Range: {self.audio_data.min():.4f} to {self.audio_data.max():.4f}")
        print(f"Audio Mean: {self.audio_data.mean():.4f}")
        print(f"Audio Std: {self.audio_data.std():.4f}")
        print("="*50)
    
    def get_audio_segment(self, start_time, end_time):
        """
        Extract a segment of audio between start and end times.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            
        Returns:
            np.array: Audio segment, or None if invalid times
        """
        if self.audio_data is None:
            print("No audio data loaded")
            return None
        
        if start_time < 0 or end_time > self.duration or start_time >= end_time:
            print(f"Invalid time range: {start_time}s to {end_time}s (duration: {self.duration}s)")
            return None
        
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        segment = self.audio_data[start_sample:end_sample]
        print(f"Extracted {end_time-start_time:.2f}s segment ({len(segment):,} samples)")
        return segment
    
    def plot_waveform(self, start_time=0, duration=30, save_plot=False):
        """
        Plot the audio waveform for visual inspection.
        
        Args:
            start_time (float): Start time in seconds for the plot
            duration (float): Duration in seconds to plot
            save_plot (bool): Whether to save the plot as an image
        """
        if self.audio_data is None:
            print("No audio data loaded")
            return
        
        end_time = min(start_time + duration, self.duration)
        audio_segment = self.get_audio_segment(start_time, end_time)
        
        if audio_segment is None:
            return
        
        # Create time axis
        time_axis = np.linspace(start_time, end_time, len(audio_segment))
        
        # Create the plot
        plt.figure(figsize=(15, 6))
        plt.plot(time_axis, audio_segment)
        plt.title(f'Audio Waveform: {Path(self.audio_file_path).name}')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Amplitude')
        plt.grid(True, alpha=0.3)
        
        # Add some useful markers
        plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        if save_plot:
            plot_name = f"waveform_{start_time}s_to_{end_time}s.png"
            plt.savefig(plot_name, dpi=300, bbox_inches='tight')
            print(f"Plot saved as: {plot_name}")
        
        plt.show()
    
    def find_loud_moments(self, threshold_percentile=95, min_gap=1.0, max_analysis_duration=300):
        """
        Find moments in the audio that are louder than a threshold.
        This can help identify significant events like inning transitions.
        
        Args:
            threshold_percentile (float): Percentile threshold for "loud" moments
            min_gap (float): Minimum gap in seconds between loud moments
            max_analysis_duration (float): Maximum duration to analyze (seconds) to speed up processing
            
        Returns:
            list: List of (start_time, end_time, peak_amplitude) tuples
        """
        if self.audio_data is None:
            print("No audio data loaded")
            return []
        
        # Limit analysis to first few minutes for faster processing
        analysis_duration = min(max_analysis_duration, self.duration)
        analysis_samples = int(analysis_duration * self.sample_rate)
        analysis_audio = self.audio_data[:analysis_samples]
        
        print(f"Analyzing first {analysis_duration:.1f} seconds for loud moments...")
        
        # Downsample for faster processing (every 10 samples)
        downsample_factor = 10
        downsampled_audio = analysis_audio[::downsample_factor]
        downsampled_rate = self.sample_rate / downsample_factor
        
        # Calculate amplitude envelope (absolute values)
        amplitude = np.abs(downsampled_audio)
        
        # Set threshold based on percentile
        threshold = np.percentile(amplitude, threshold_percentile)
        print(f"Loud moment threshold: {threshold:.4f} ({threshold_percentile}th percentile)")
        
        # Find samples above threshold
        loud_samples = amplitude > threshold
        
        # Convert to time indices using vectorized operations
        loud_times = []
        
        # Find transitions (where loud_samples changes from False to True or vice versa)
        transitions = np.diff(loud_samples.astype(int))
        start_indices = np.where(transitions == 1)[0] + 1  # +1 because diff shifts indices
        end_indices = np.where(transitions == -1)[0] + 1
        
        # Handle edge cases
        if loud_samples[0]:  # Audio starts loud
            start_indices = np.concatenate([[0], start_indices])
        if loud_samples[-1]:  # Audio ends loud
            end_indices = np.concatenate([end_indices, [len(loud_samples)]])
        
        # Convert indices to times
        for start_idx, end_idx in zip(start_indices, end_indices):
            start_time = start_idx / downsampled_rate
            end_time = end_idx / downsampled_rate
            
            # Check minimum gap
            if not loud_times or (start_time - loud_times[-1][1]) > min_gap:
                # Calculate peak amplitude in original audio
                orig_start = int(start_time * self.sample_rate)
                orig_end = int(end_time * self.sample_rate)
                if orig_end > orig_start:
                    peak_amp = np.max(np.abs(self.audio_data[orig_start:orig_end]))
                else:
                    peak_amp = abs(self.audio_data[orig_start])
                
                loud_times.append((start_time, end_time, peak_amp))
        
        print(f"Found {len(loud_times)} loud moments:")
        for i, (start, end, peak) in enumerate(loud_times[:10]):  # Show first 10
            print(f"  {i+1}: {start:.2f}s - {end:.2f}s (peak: {peak:.4f})")
        
        if len(loud_times) > 10:
            print(f"  ... and {len(loud_times) - 10} more")
        
        return loud_times


def test_audio_loading():
    """
    Test function to load and analyze the downloaded Dinger City audio.
    """
    # Path to our downloaded audio file
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    
    print("Mario Baseball Audio Analysis Test")
    print("=" * 40)
    
    # Create analyzer and load audio
    analyzer = AudioAnalyzer()
    
    if analyzer.load_audio(audio_file):
        print("\n[AUDIO] Audio loaded successfully! Let's explore the data...")
        
        # Find loud moments that might be inning transitions or significant events
        print("\n[ANALYSIS] Looking for loud moments (potential game events)...")
        loud_moments = analyzer.find_loud_moments(threshold_percentile=90, min_gap=2.0)
        
        # Show first few minutes of waveform
        print("\n[PLOT] Generating waveform plot of first 60 seconds...")
        try:
            analyzer.plot_waveform(start_time=0, duration=60, save_plot=True)
        except Exception as e:
            print(f"Plotting not available in this environment: {e}")
            print("(This is normal in terminal environments)")
        
        # Extract a small sample to understand data structure
        print("\n[SAMPLES] Extracting sample audio segments...")
        sample_1 = analyzer.get_audio_segment(0, 5)  # First 5 seconds
        sample_2 = analyzer.get_audio_segment(60, 65)  # 1 minute mark
        
        if sample_1 is not None:
            print(f"Sample 1 (0-5s): Shape {sample_1.shape}, Range {sample_1.min():.4f} to {sample_1.max():.4f}")
        if sample_2 is not None:
            print(f"Sample 2 (60-65s): Shape {sample_2.shape}, Range {sample_2.min():.4f} to {sample_2.max():.4f}")
        
        print("\n[COMPLETE] Audio analysis complete! Ready for pattern matching.")
        return analyzer
    else:
        print("[ERROR] Failed to load audio file")
        return None


if __name__ == "__main__":
    # Run test when script is executed directly
    test_audio_loading()