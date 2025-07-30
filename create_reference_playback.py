"""
Create audio playback files to verify our reference pattern is correct.
This will help debug why the pattern matching isn't working on the new video.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

def create_reference_playback():
    """
    Create playable audio files of our reference pattern and original examples
    so you can verify they sound correct.
    """
    print("Creating Reference Pattern Playback Files")
    print("=" * 50)
    
    output_dir = Path("reference_playback")
    output_dir.mkdir(exist_ok=True)
    
    print("This will create audio files you can play to verify our reference pattern.")
    
    # 1. Load and save the current reference pattern
    print("\n1. Current Reference Pattern:")
    try:
        pattern_file = "reference_sounds/refined_inning_transition_pattern.wav"
        reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
        
        # Save at higher sample rate for better playability
        output_file = output_dir / "current_reference_pattern.wav"
        sf.write(str(output_file), reference_pattern, 22050)
        
        print(f"   [SAVED] {output_file}")
        print(f"   Duration: {len(reference_pattern)/ref_sr:.2f} seconds")
        print(f"   This is the averaged pattern from all 5 examples")
        
    except Exception as e:
        print(f"   [ERROR] Could not load reference pattern: {e}")
    
    # 2. Load and save all individual examples from the original video
    print("\n2. Individual Examples from Original Video:")
    
    original_examples = [
        {"file": "complete_example_1_1st_top_to_bottom_2-28.wav", "desc": "2:28 - Top 1st to Bottom 1st"},
        {"file": "complete_example_2_1st_bottom_to_2nd_top_3-19.wav", "desc": "3:19 - Bottom 1st to Top 2nd"},
        {"file": "complete_example_3_2nd_top_to_bottom_4-03.wav", "desc": "4:03 - Top 2nd to Bottom 2nd"},
        {"file": "complete_example_4_2nd_bottom_to_3rd_top_5-14.wav", "desc": "5:14 - Bottom 2nd to Top 3rd"},
        {"file": "complete_example_5_3rd_top_to_bottom_7-34.wav", "desc": "7:34 - Top 3rd to Bottom 3rd"},
    ]
    
    for i, example in enumerate(original_examples):
        try:
            source_file = Path("reference_sounds") / example["file"]
            if source_file.exists():
                audio_data, sr = librosa.load(str(source_file), sr=22050)
                
                output_file = output_dir / f"original_example_{i+1}_{example['file']}"
                sf.write(str(output_file), audio_data, 22050)
                
                print(f"   [SAVED] original_example_{i+1}_{example['file']}")
                print(f"           {example['desc']}")
            else:
                print(f"   [MISSING] {example['file']}")
                
        except Exception as e:
            print(f"   [ERROR] Could not process {example['file']}: {e}")
    
    # 3. Extract and save audio from suspected locations in the new video
    print("\n3. Extracting Audio from New Video at Suspected Locations:")
    
    try:
        # Find the new video file
        temp_dir = Path("temp_audio_new")
        audio_files = list(temp_dir.glob("*.webm"))
        
        if audio_files:
            new_video_file = str(audio_files[0])
            print(f"   Source: New video file")
            
            # Extract audio from the timestamps we detected (but were wrong)
            suspect_times = [35, 255, 423]  # 0:35, 4:15, 7:03 in seconds
            
            for i, time_sec in enumerate(suspect_times):
                mm = time_sec // 60
                ss = time_sec % 60
                
                try:
                    # Load 4-second window around the time
                    audio_segment, sr = librosa.load(
                        new_video_file,
                        sr=22050,
                        offset=max(0, time_sec - 1),
                        duration=4.0
                    )
                    
                    output_file = output_dir / f"new_video_suspect_{i+1}_{mm:02d}-{ss:02d}.wav"
                    sf.write(str(output_file), audio_segment, 22050)
                    
                    print(f"   [SAVED] new_video_suspect_{i+1}_{mm:02d}-{ss:02d}.wav")
                    print(f"           4-second clip around {mm}:{ss:02d}")
                    
                except Exception as e:
                    print(f"   [ERROR] Could not extract audio at {mm}:{ss:02d}: {e}")
        else:
            print("   [ERROR] No new video file found")
            
    except Exception as e:
        print(f"   [ERROR] Could not process new video: {e}")
    
    # 4. Instructions for verification
    print(f"\n4. VERIFICATION INSTRUCTIONS:")
    print(f"   Playback files saved to: {output_dir}")
    print(f"   ")
    print(f"   Please listen to these files and verify:")
    print(f"   ")
    print(f"   A. Reference Pattern Verification:")
    print(f"      - Play 'current_reference_pattern.wav'")
    print(f"      - Does this sound like the Mario Baseball inning transition?")
    print(f"      - Is it clear and recognizable?")
    print(f"   ")
    print(f"   B. Original Examples Verification:")
    print(f"      - Play 'original_example_1_...' through 'original_example_5_...'")
    print(f"      - Do these all sound like the same type of sound?")
    print(f"      - Are they all clearly inning transitions?")
    print(f"   ")
    print(f"   C. New Video Suspects:")
    print(f"      - Play 'new_video_suspect_1_00-35.wav' (what we detected at 0:35)")
    print(f"      - Play 'new_video_suspect_2_04-15.wav' (what we detected at 4:15)")
    print(f"      - Play 'new_video_suspect_3_07-03.wav' (what we detected at 7:03)")
    print(f"      - Do any of these sound like inning transitions?")
    print(f"      - How do they compare to the reference pattern?")
    print(f"   ")
    print(f"   NEXT STEPS based on what you hear:")
    print(f"   - If reference pattern sounds wrong: We need to rebuild it")
    print(f"   - If reference pattern sounds right but new video clips don't match:")
    print(f"     We need to manually find inning transitions in the new video")
    print(f"   - If new video has very different audio: May need video-specific patterns")
    
    return output_dir

if __name__ == "__main__":
    playback_dir = create_reference_playback()
    print(f"\nPlayback files ready in: {playback_dir}")
    print("Please listen and report what you hear!")