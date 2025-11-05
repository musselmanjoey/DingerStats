"""
Audio Filtering System to Separate Commentary from Game Sounds

This module applies various audio processing techniques to isolate
game sounds from commentary in Dinger City videos, improving
inning transition detection accuracy.
"""

import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path
import matplotlib.pyplot as plt

class AudioFilter:
    def __init__(self):
        """
        Initialize the audio filtering system.
        """
        self.sample_rate = 22050
        
    def load_audio(self, file_path, duration=None):
        """
        Load audio file for filtering.
        """
        audio_data, sr = librosa.load(file_path, sr=self.sample_rate, duration=duration)
        return audio_data, sr
    
    def spectral_subtraction_filter(self, audio_data, noise_reduction=0.5):
        """
        Use spectral subtraction to reduce commentary.
        This estimates the noise (commentary) profile and subtracts it.
        """
        print("Applying spectral subtraction filter...")
        
        # Convert to frequency domain
        stft = librosa.stft(audio_data, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor (first 2 seconds assumed to have commentary)
        noise_frames = int(2.0 * self.sample_rate / 512)  # 2 seconds worth of frames
        noise_profile = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Spectral subtraction
        magnitude_cleaned = magnitude - (noise_reduction * noise_profile)
        
        # Ensure we don't go below 10% of original magnitude
        magnitude_cleaned = np.maximum(magnitude_cleaned, 0.1 * magnitude)
        
        # Reconstruct audio
        stft_cleaned = magnitude_cleaned * np.exp(1j * phase)
        audio_cleaned = librosa.istft(stft_cleaned, hop_length=512)
        
        return audio_cleaned
    
    def frequency_band_filter(self, audio_data):
        """
        Filter to emphasize frequency bands where game sounds typically occur.
        Game sounds often have more mid-high frequency content than speech.
        """
        print("Applying frequency band filter...")
        
        # Design bandpass filter for game sounds (approximately 1kHz - 8kHz)
        # Commentary is typically 100Hz - 3kHz, so we emphasize higher frequencies
        
        # High-pass filter to reduce low-frequency speech
        sos_hp = signal.butter(4, 800, btype='high', fs=self.sample_rate, output='sos')
        audio_hp = signal.sosfilt(sos_hp, audio_data)
        
        # Slight low-pass to remove very high frequency noise
        sos_lp = signal.butter(4, 10000, btype='low', fs=self.sample_rate, output='sos')
        audio_filtered = signal.sosfilt(sos_lp, audio_hp)
        
        return audio_filtered
    
    def dynamic_range_compression(self, audio_data, threshold=0.3, ratio=4.0):
        """
        Apply compression to normalize dynamic range.
        This helps even out volume differences between commentary and game sounds.
        """
        print("Applying dynamic range compression...")
        
        # Simple compression algorithm
        compressed = np.copy(audio_data)
        
        # Find samples above threshold
        above_threshold = np.abs(compressed) > threshold
        
        # Apply compression to loud samples
        compressed[above_threshold] = (
            np.sign(compressed[above_threshold]) * 
            (threshold + (np.abs(compressed[above_threshold]) - threshold) / ratio)
        )
        
        return compressed
    
    def adaptive_noise_gate(self, audio_data, gate_threshold=0.02, attack_time=0.01, release_time=0.1):
        """
        Apply noise gate to reduce quiet commentary between game sounds.
        """
        print("Applying adaptive noise gate...")
        
        # Convert time to samples
        attack_samples = int(attack_time * self.sample_rate)
        release_samples = int(release_time * self.sample_rate)
        
        # Calculate envelope
        envelope = np.abs(audio_data)
        
        # Smooth envelope
        window_size = int(0.01 * self.sample_rate)  # 10ms window
        envelope_smooth = np.convolve(envelope, np.ones(window_size)/window_size, mode='same')
        
        # Generate gate signal
        gate = np.ones_like(audio_data)
        
        # Apply gating based on envelope
        below_threshold = envelope_smooth < gate_threshold
        gate[below_threshold] = 0.1  # Reduce to 10% instead of complete silence
        
        # Smooth gate transitions
        gate = np.convolve(gate, np.ones(attack_samples)/attack_samples, mode='same')
        
        return audio_data * gate
    
    def apply_combined_filter(self, audio_data, filter_config=None):
        """
        Apply a combination of filtering techniques.
        """
        if filter_config is None:
            filter_config = {
                'spectral_subtraction': True,
                'frequency_band': True,
                'compression': True,
                'noise_gate': True
            }
        
        print("Applying combined audio filtering...")
        filtered_audio = np.copy(audio_data)
        
        # Apply filters in sequence
        if filter_config.get('frequency_band', True):
            filtered_audio = self.frequency_band_filter(filtered_audio)
        
        if filter_config.get('spectral_subtraction', True):
            filtered_audio = self.spectral_subtraction_filter(filtered_audio, noise_reduction=0.3)
        
        if filter_config.get('compression', True):
            filtered_audio = self.dynamic_range_compression(filtered_audio)
        
        if filter_config.get('noise_gate', True):
            filtered_audio = self.adaptive_noise_gate(filtered_audio)
        
        # Normalize output
        max_val = np.max(np.abs(filtered_audio))
        if max_val > 0:
            filtered_audio = filtered_audio / max_val * 0.8  # Leave some headroom
        
        return filtered_audio
    
    def save_filtered_audio(self, audio_data, output_path):
        """
        Save filtered audio to file.
        """
        sf.write(output_path, audio_data, self.sample_rate)
        print(f"[SAVED] Filtered audio: {output_path}")

def test_audio_filtering():
    """
    Test the audio filtering system on both videos.
    """
    print("Testing Audio Filtering System")
    print("=" * 40)
    
    filter_system = AudioFilter()
    
    # Test on both videos
    video_files = [
        {
            "name": "Original Video",
            "path": "temp_audio/The CRAZIEST hit in Mario Baseball.webm",
            "test_segment": (140, 160)  # Around 2:28 where we know there's a transition
        },
        {
            "name": "New Video", 
            "path": "temp_audio_new/Is Monty Mole enough to make the playoffs？？.webm",
            "test_segment": (30, 50)  # Around 0:35 where we detected something
        }
    ]
    
    output_dir = Path("filtered_audio_samples")
    output_dir.mkdir(exist_ok=True)
    
    for video in video_files:
        print(f"\n{video['name']}:")
        print("-" * 30)
        
        try:
            # Load test segment
            start_time, end_time = video['test_segment']
            print(f"Loading segment: {start_time}s to {end_time}s")
            
            audio_data, sr = filter_system.load_audio(
                video['path'],
                duration=None  # Load full file first
            )
            
            # Extract test segment
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            test_segment = audio_data[start_sample:end_sample]
            
            print(f"Test segment: {len(test_segment)/sr:.1f} seconds")
            
            # Save original segment
            original_file = output_dir / f"{video['name'].lower().replace(' ', '_')}_original.wav"
            filter_system.save_filtered_audio(test_segment, str(original_file))
            
            # Apply different filtering approaches
            filter_configs = [
                {"name": "frequency_only", "config": {"spectral_subtraction": False, "frequency_band": True, "compression": False, "noise_gate": False}},
                {"name": "spectral_only", "config": {"spectral_subtraction": True, "frequency_band": False, "compression": False, "noise_gate": False}},
                {"name": "combined_light", "config": {"spectral_subtraction": True, "frequency_band": True, "compression": False, "noise_gate": False}},
                {"name": "combined_full", "config": {"spectral_subtraction": True, "frequency_band": True, "compression": True, "noise_gate": True}},
            ]
            
            for filter_set in filter_configs:
                print(f"  Testing: {filter_set['name']}")
                
                filtered_audio = filter_system.apply_combined_filter(
                    test_segment, 
                    filter_set['config']
                )
                
                # Save filtered version
                filtered_file = output_dir / f"{video['name'].lower().replace(' ', '_')}_{filter_set['name']}.wav"
                filter_system.save_filtered_audio(filtered_audio, str(filtered_file))
                
        except Exception as e:
            print(f"  [ERROR] Failed to process {video['name']}: {e}")
    
    print(f"\n{'='*40}")
    print("FILTERING TEST COMPLETE")
    print(f"{'='*40}")
    print(f"Audio samples saved to: {output_dir}")
    print()
    print("Please listen to the filtered versions and compare:")
    print("1. Does filtering make the game sounds clearer?")
    print("2. Which filtering approach works best?")
    print("3. Can you hear the inning transition sound better?")
    print()
    print("Once you identify the best filtering approach,")
    print("we'll apply it to full pattern matching!")

if __name__ == "__main__":
    test_audio_filtering()