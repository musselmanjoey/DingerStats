"""
Extract samples around inning transitions to find the "change" announcement pattern.
"""

import librosa
import soundfile as sf
from pathlib import Path

def extract_change_samples():
    """
    Extract 10-second samples around known transitions to analyze the 'change' pattern.
    """
    print("EXTRACTING 'CHANGE' ANNOUNCEMENT SAMPLES")
    print("=" * 50)
    
    # Known transitions - good ones and the missed 9th inning ones
    transitions = [
        {"time": 147, "description": "End of 1st (2:27) - GOOD DETECTION"},
        {"time": 199, "description": "3:19 - Known from manual analysis"},
        {"time": 243, "description": "4:03 - Detected as weak signal"},
        {"time": 313, "description": "5:13 - GOOD DETECTION"},
        {"time": 455, "description": "7:35 - GOOD DETECTION"},
        {"time": 1119, "description": "18:39 - Top of 9th (MISSED)"},
        {"time": 1174, "description": "19:34 - Bottom of 9th (MISSED)"},
    ]
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    output_dir = Path("change_samples")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Loading video audio...")
    
    for i, transition in enumerate(transitions):
        time_sec = transition["time"]
        description = transition["description"]
        mm, ss = time_sec // 60, time_sec % 60
        
        print(f"\n{i+1}. {mm}:{ss:02d} - {description}")
        
        try:
            # Extract 10-second window: 5 seconds before to 5 seconds after
            start_time = max(0, time_sec - 5)
            duration = 10
            
            audio_segment, sr = librosa.load(
                audio_file, 
                sr=22050, 
                offset=start_time, 
                duration=duration
            )
            
            # Save the sample
            filename = f"sample_{i+1:02d}_{mm:02d}m{ss:02d}s_{'good' if 'GOOD' in description else 'missed' if 'MISSED' in description else 'weak'}.wav"
            output_path = output_dir / filename
            
            sf.write(str(output_path), audio_segment, sr)
            print(f"   Saved: {filename} ({len(audio_segment)/sr:.1f}s)")
            
            # Also analyze the pre-transition period (where 'change' should be)
            if time_sec >= 3:
                pre_transition_start = time_sec - 3
                pre_audio, _ = librosa.load(
                    audio_file,
                    sr=22050,
                    offset=pre_transition_start,
                    duration=3
                )
                
                pre_filename = f"pre_{i+1:02d}_{mm:02d}m{ss:02d}s_change_area.wav"
                pre_output_path = output_dir / pre_filename
                
                sf.write(str(pre_output_path), pre_audio, sr)
                print(f"   Pre-transition (change area): {pre_filename}")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print(f"\nSamples saved to: {output_dir}")
    print("\nLISTEN TO THESE FILES TO IDENTIFY:")
    print("1. The 'change' announcement pattern (should be 1-2s before inning chime)")
    print("2. Differences between good detections vs missed ones")
    print("3. Any consistent audio patterns we can use")
    
    # Quick analysis of timing patterns
    print(f"\nTIMING ANALYSIS:")
    print("Expected 9th inning transitions:")
    print(f"  18:39 (1119s) - Should be top of 9th")
    print(f"  19:34 (1174s) - Should be bottom of 9th")
    print(f"  Gap: {1174-1119} seconds = {(1174-1119)/60:.1f} minutes")
    
    detected_near_9th = [
        ("18:07", 1087.5),
        ("19:32", 1172.7)
    ]
    
    print(f"\nActual detections near 9th inning:")
    for time_str, time_sec in detected_near_9th:
        error_top = abs(time_sec - 1119)
        error_bottom = abs(time_sec - 1174)
        print(f"  {time_str} ({time_sec}s) - Error from top 9th: {error_top:.1f}s, from bottom 9th: {error_bottom:.1f}s")

if __name__ == "__main__":
    extract_change_samples()