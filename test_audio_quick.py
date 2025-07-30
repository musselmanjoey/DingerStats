"""
Quick test of audio loading to verify librosa is working properly.
"""

import librosa
import numpy as np
from pathlib import Path

def quick_audio_test():
    """
    Quick test with just the basic audio loading to verify it works.
    """
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    
    print("Quick Audio Loading Test")
    print("=" * 30)
    
    try:
        print(f"Loading: {audio_file}")
        print("This may take a moment for WebM files...")
        
        # Load just first 30 seconds to test
        audio_data, sample_rate = librosa.load(audio_file, sr=22050, duration=30.0)
        
        print(f"SUCCESS! Audio loaded:")
        print(f"  Duration: 30.0 seconds (test clip)")
        print(f"  Sample Rate: {sample_rate:,} Hz")
        print(f"  Total Samples: {len(audio_data):,}")
        print(f"  Audio Shape: {audio_data.shape}")
        print(f"  Audio Range: {audio_data.min():.4f} to {audio_data.max():.4f}")
        
        # Simple analysis - find some loud moments in first 30 seconds
        amplitude = np.abs(audio_data)
        threshold = np.percentile(amplitude, 95)
        loud_samples = amplitude > threshold
        loud_count = np.sum(loud_samples)
        
        print(f"  Loud samples (95th percentile): {loud_count:,} / {len(audio_data):,}")
        print(f"  Percentage loud: {100 * loud_count / len(audio_data):.2f}%")
        
        print("\n[SUCCESS] Librosa is working correctly!")
        print("[SUCCESS] Audio data structure understood!")
        print("[SUCCESS] Ready for inning detection development!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    quick_audio_test()