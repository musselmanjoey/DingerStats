"""
Extract longer audio windows for manual Audacity sample creation.
Creates 8-10 second windows around known transitions containing both 
'change' announcement and inning chime for precise manual extraction.
"""

import librosa
import soundfile as sf
from pathlib import Path

def extract_audacity_windows():
    """
    Extract longer audio windows around all known transitions for Audacity editing.
    """
    print("EXTRACTING AUDIO WINDOWS FOR AUDACITY SAMPLE CREATION")
    print("=" * 60)
    
    # All known transitions - good detections and missed ones
    transitions = [
        {"time": 147, "desc": "2:27 - End of 1st inning (GOOD DETECTION)", "priority": "high"},
        {"time": 199, "desc": "3:19 - Bottom 1st to Top 2nd (WEAK SIGNAL)", "priority": "medium"},
        {"time": 243, "desc": "4:03 - Top 2nd to Bottom 2nd (WEAK SIGNAL)", "priority": "medium"},
        {"time": 313, "desc": "5:13 - Bottom 2nd to Top 3rd (GOOD DETECTION)", "priority": "high"},
        {"time": 455, "desc": "7:35 - Top 3rd to Bottom 3rd (GOOD DETECTION)", "priority": "high"},
        {"time": 1119, "desc": "18:39 - Top of 9th inning (MISSED)", "priority": "high"},
        {"time": 1174, "desc": "19:34 - Bottom of 9th inning (MISSED)", "priority": "high"},
    ]
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    output_dir = Path("audacity_windows")
    output_dir.mkdir(exist_ok=True)
    
    print(f"Extracting {len(transitions)} audio windows for manual sample creation...")
    print("Each window: 8 seconds (4 seconds before + 4 seconds after transition)")
    print("Should contain: [commentary] -> 'change' announcement -> inning chime -> [next audio]")
    
    for i, transition in enumerate(transitions):
        time_sec = transition["time"]
        description = transition["desc"]
        priority = transition["priority"]
        mm, ss = time_sec // 60, time_sec % 60
        
        print(f"\n{i+1}. {description}")
        print(f"   Time: {mm}:{ss:02d} ({time_sec}s) - Priority: {priority}")
        
        try:
            # Extract 8-second window: 4 seconds before to 4 seconds after
            start_time = max(0, time_sec - 4)
            duration = 8
            
            audio_segment, sr = librosa.load(
                audio_file, 
                sr=22050,  # Keep high quality for Audacity work
                offset=start_time, 
                duration=duration
            )
            
            # Create descriptive filename
            priority_prefix = "A_" if priority == "high" else "B_"
            status = "good" if "GOOD" in description else "missed" if "MISSED" in description else "weak"
            filename = f"{priority_prefix}{i+1:02d}_{mm:02d}m{ss:02d}s_{status}_8sec_window.wav"
            output_path = output_dir / filename
            
            sf.write(str(output_path), audio_segment, sr)
            
            actual_duration = len(audio_segment) / sr
            print(f"   Saved: {filename}")
            print(f"   Window: {start_time:.1f}s to {start_time + actual_duration:.1f}s ({actual_duration:.1f}s)")
            
            # Also create a shorter 5-second focused window for the core transition
            focused_start = max(0, time_sec - 2.5)
            focused_duration = 5
            
            focused_audio, _ = librosa.load(
                audio_file,
                sr=22050,
                offset=focused_start,
                duration=focused_duration
            )
            
            focused_filename = f"{priority_prefix}{i+1:02d}_{mm:02d}m{ss:02d}s_{status}_5sec_focused.wav"
            focused_output_path = output_dir / focused_filename
            
            sf.write(str(focused_output_path), focused_audio, sr)
            print(f"   Focused: {focused_filename} (5s centered on transition)")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print(f"\n" + "=" * 60)
    print("AUDACITY WORKFLOW INSTRUCTIONS:")
    print("=" * 60)
    print("Files saved to:", output_dir)
    print()
    print("FILE NAMING:")
    print("- A_XX = High priority (good detections + missed 9th inning)")
    print("- B_XX = Medium priority (weak signals)")
    print("- 8sec_window = Full context for analysis")
    print("- 5sec_focused = Tighter window around transition")
    print()
    print("AUDACITY STEPS:")
    print("1. Open high priority files (A_XX) first")
    print("2. Listen for the sequence: [commentary] -> 'CHANGE' -> [chime]")
    print("3. Use Selection Tool to highlight just the 'CHANGE' announcement")
    print("4. Export as 'change_sample_XX.wav'")
    print("5. Select just the inning chime (no commentary)")
    print("6. Export as 'chime_sample_XX.wav'")
    print("7. Repeat for multiple samples to create a library")
    print()
    print("TARGET SAMPLES TO CREATE:")
    print("- 3-5 clean 'change' announcement samples")
    print("- 3-5 clean inning chime samples")
    print("- Try to get samples from different innings for variety")
    
    return transitions

if __name__ == "__main__":
    extract_audacity_windows()