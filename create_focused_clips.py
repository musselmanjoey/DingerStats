"""
Create focused audio clips around the exact inning transition timing.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

class FocusedClipCreator:
    def __init__(self):
        self.sample_rate = 22050
        
    def create_focused_clips(self):
        """
        Create 6-second clips centered around the transition at 8 seconds.
        """
        print("Creating Focused Audio Clips")
        print("=" * 35)
        
        # The transition happens at 8 seconds in our 20-second original clip
        # Original clip was from 140s-160s, so transition is at 148s in full video
        transition_offset = 8.0  # 8 seconds into our test clip
        
        # Create 6-second clips: 3 seconds before + 3 seconds after transition
        clip_duration = 6.0
        before_transition = 3.0
        
        from audio_filtering import AudioFilter
        filter_system = AudioFilter()
        
        video_files = [
            {
                "name": "Original Video",
                "path": "temp_audio/The CRAZIEST hit in Mario Baseball.webm",
                "full_video_transition_time": 148.0  # 2:28 in full video
            },
            {
                "name": "New Video", 
                "path": "temp_audio_new/Is Monty Mole enough to make the playoffs？？.webm",
                "full_video_transition_time": 35.0  # Our suspected time
            }
        ]
        
        output_dir = Path("focused_clips")
        output_dir.mkdir(exist_ok=True)
        
        for video in video_files:
            print(f"\n{video['name']}:")
            print("-" * 25)
            
            try:
                # Load full audio file
                audio_data, sr = filter_system.load_audio(video['path'])
                
                # Calculate clip boundaries
                center_time = video['full_video_transition_time']
                start_time = center_time - before_transition
                end_time = center_time + before_transition
                
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                
                # Extract focused clip
                focused_clip = audio_data[start_sample:end_sample]
                
                print(f"Extracting {clip_duration}s clip centered at {center_time}s")
                print(f"Clip range: {start_time:.1f}s to {end_time:.1f}s")
                print(f"Clip length: {len(focused_clip)/sr:.1f} seconds")
                
                # Save original focused clip
                video_name = video['name'].lower().replace(' ', '_')
                original_file = output_dir / f"{video_name}_focused_original.wav"
                sf.write(str(original_file), focused_clip, sr)
                print(f"[SAVED] {original_file}")
                
                # Apply different filtering approaches to focused clip
                filter_configs = [
                    {"name": "frequency_only", "config": {"spectral_subtraction": False, "frequency_band": True, "compression": False, "noise_gate": False}},
                    {"name": "spectral_only", "config": {"spectral_subtraction": True, "frequency_band": False, "compression": False, "noise_gate": False}},
                    {"name": "combined_light", "config": {"spectral_subtraction": True, "frequency_band": True, "compression": False, "noise_gate": False}},
                    {"name": "combined_full", "config": {"spectral_subtraction": True, "frequency_band": True, "compression": True, "noise_gate": True}},
                ]
                
                for filter_set in filter_configs:
                    print(f"  Applying: {filter_set['name']}")
                    
                    filtered_audio = filter_system.apply_combined_filter(
                        focused_clip, 
                        filter_set['config']
                    )
                    
                    # Save filtered version
                    filtered_file = output_dir / f"{video_name}_focused_{filter_set['name']}.wav"
                    sf.write(str(filtered_file), filtered_audio, sr)
                    print(f"  [SAVED] {filtered_file}")
                
            except Exception as e:
                print(f"  [ERROR] Failed to process {video['name']}: {e}")
        
        # Also create a clip of our official reference for comparison
        print(f"\nOfficial Reference:")
        print("-" * 20)
        
        try:
            reference_audio, ref_sr = librosa.load(
                "reference_sounds/official_inning_transition_pattern.wav", 
                sr=22050
            )
            
            # Save official reference in focused clips folder for easy comparison
            ref_file = output_dir / "official_next_inning_reference.wav"
            sf.write(str(ref_file), reference_audio, ref_sr)
            print(f"[SAVED] {ref_file}")
            print(f"Duration: {len(reference_audio)/ref_sr:.2f} seconds")
            
        except Exception as e:
            print(f"[ERROR] Could not copy reference: {e}")
        
        print(f"\n{'='*35}")
        print("FOCUSED CLIPS CREATED")
        print(f"{'='*35}")
        print(f"All clips saved to: {output_dir}")
        print()
        print("Now you have 6-second focused clips to compare:")
        print("- Transition should occur around 3-second mark in each clip")
        print("- Much easier to hear the exact timing")
        print("- Compare filtered versions to find best approach")
        print()
        print("Listen for the official 'Next Inning' reference sound")
        print("in the filtered clips!")

if __name__ == "__main__":
    creator = FocusedClipCreator()
    creator.create_focused_clips()