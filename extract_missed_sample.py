"""
Extract audio sample from the missed 18:39 transition for manual Audacity editing.
"""

import librosa
import soundfile as sf
from pathlib import Path

def extract_18_39_sample():
    """
    Extract a focused sample around 18:39 for the missed 9th inning transition.
    """
    print("EXTRACTING 18:39 SAMPLE FOR AUDACITY")
    print("=" * 40)
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    output_dir = Path("better_samples")
    
    # 18:39 = 18*60 + 39 = 1119 seconds
    target_time = 1119
    
    print(f"Target time: 18:39 ({target_time}s)")
    print("Extracting multiple window sizes for analysis...")
    
    try:
        # Extract different window sizes for analysis
        windows = [
            {"duration": 8, "offset": 4, "desc": "8sec_window"},
            {"duration": 5, "offset": 2.5, "desc": "5sec_focused"}, 
            {"duration": 3, "offset": 1.5, "desc": "3sec_tight"}
        ]
        
        for window in windows:
            duration = window["duration"]
            offset = window["offset"]
            desc = window["desc"]
            
            start_time = max(0, target_time - offset)
            
            audio_segment, sr = librosa.load(
                audio_file,
                sr=22050,
                offset=start_time,
                duration=duration
            )
            
            filename = f"sample_18m39s_{desc}.wav"
            output_path = output_dir / filename
            
            sf.write(str(output_path), audio_segment, sr)
            
            actual_duration = len(audio_segment) / sr
            print(f"[OK] {filename}: {start_time:.1f}s to {start_time + actual_duration:.1f}s ({actual_duration:.1f}s)")
        
        print(f"\nFiles saved to: {output_dir}")
        print("\nAUDACITY INSTRUCTIONS:")
        print("1. Open sample_18m39s_5sec_focused.wav (recommended starting point)")
        print("2. Listen for the inning chime")
        print("3. Select just the chime (avoid commentary)")
        print("4. Export as 'chime_sample_06.wav'")
        print("5. This will be our 6th chime template")
        
        print(f"\nWHY THIS SAMPLE MATTERS:")
        print("- This was missed by current system (no consensus)")
        print("- Adding it should improve detection of similar 9th inning patterns")
        print("- Will help us reach 90%+ accuracy target")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    extract_18_39_sample()