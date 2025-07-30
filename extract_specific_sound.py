"""
Extract specific inning transition sound based on user identification.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

def extract_inning_sound(start_time_minutes, start_time_seconds, end_time_minutes, end_time_seconds):
    """
    Extract the inning transition sound from specific timestamps.
    
    Args:
        start_time_minutes (int): Start minutes
        start_time_seconds (int): Start seconds  
        end_time_minutes (int): End minutes
        end_time_seconds (int): End seconds
    """
    # Convert to total seconds
    start_time = start_time_minutes * 60 + start_time_seconds
    end_time = end_time_minutes * 60 + end_time_seconds
    
    print(f"Extracting inning sound from {start_time_minutes}:{start_time_seconds:02d} to {end_time_minutes}:{end_time_seconds:02d}")
    print(f"That's {start_time}s to {end_time}s")
    
    # Load audio file
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    
    try:
        print("Loading audio...")
        # Load the specific segment with some padding
        padding = 1.0  # 1 second padding on each side
        audio_data, sample_rate = librosa.load(
            audio_file,
            sr=22050,
            offset=max(0, start_time - padding),
            duration=(end_time - start_time) + (2 * padding)
        )
        
        print(f"Loaded {len(audio_data)/sample_rate:.2f} seconds of audio")
        print(f"Sample rate: {sample_rate:,} Hz")
        
        # Calculate the exact segment within the loaded audio
        if start_time >= padding:
            segment_start = int(padding * sample_rate)
        else:
            segment_start = int(start_time * sample_rate)
            
        segment_end = segment_start + int((end_time - start_time) * sample_rate)
        
        # Extract the exact inning sound (without padding)
        inning_sound = audio_data[segment_start:segment_end]
        
        # Also extract with padding for context
        padded_sound = audio_data
        
        # Create reference_sounds directory
        output_dir = Path("reference_sounds")
        output_dir.mkdir(exist_ok=True)
        
        # Save the exact inning sound
        exact_filename = output_dir / "inning_transition_exact.wav"
        sf.write(str(exact_filename), inning_sound, sample_rate)
        print(f"[SAVED] Exact inning sound: {exact_filename}")
        print(f"        Duration: {len(inning_sound)/sample_rate:.2f} seconds")
        
        # Save with padding for context
        context_filename = output_dir / f"inning_transition_context_{start_time_minutes}-{start_time_seconds:02d}_to_{end_time_minutes}-{end_time_seconds:02d}.wav"
        sf.write(str(context_filename), padded_sound, sample_rate)
        print(f"[SAVED] With context: {context_filename}")
        print(f"        Duration: {len(padded_sound)/sample_rate:.2f} seconds")
        
        # Analyze the sound characteristics
        print(f"\nINNING SOUND CHARACTERISTICS:")
        print(f"Duration: {len(inning_sound)/sample_rate:.3f} seconds")
        print(f"Peak amplitude: {np.max(np.abs(inning_sound)):.4f}")
        print(f"RMS amplitude: {np.sqrt(np.mean(inning_sound**2)):.4f}")
        print(f"Sample count: {len(inning_sound):,}")
        
        return inning_sound, sample_rate
        
    except Exception as e:
        print(f"Error extracting sound: {str(e)}")
        return None, None

if __name__ == "__main__":
    print("Extracting User-Identified Inning Transition Sound")
    print("=" * 50)
    
    # Extract the sound from 2:28 to 2:30
    inning_sound, sr = extract_inning_sound(2, 28, 2, 30)
    
    if inning_sound is not None:
        print("\n[SUCCESS] Inning transition sound extracted!")
        print("\nThis will be our reference pattern for automated detection.")
        print("Finding more examples will help improve pattern matching accuracy.")
    else:
        print("\n[ERROR] Failed to extract inning sound")