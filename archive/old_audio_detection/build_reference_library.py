"""
Build Reference Library of Inning Transition Sounds

This script extracts multiple examples of the inning transition sound
to create a robust reference pattern for automated detection.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

# Inning transition timestamps from manual identification
inning_transitions = [
    {"inning": 1, "time_mm_ss": "2:28", "time_seconds": 2*60 + 28},  # 148 seconds
    {"inning": 2, "time_mm_ss": "4:03", "time_seconds": 4*60 + 3},   # 243 seconds  
    {"inning": 3, "time_mm_ss": "7:34", "time_seconds": 7*60 + 34},  # 454 seconds
]

def time_to_seconds(time_str):
    """Convert 'mm:ss' format to total seconds"""
    parts = time_str.split(':')
    minutes = int(parts[0])
    seconds = int(parts[1])
    return minutes * 60 + seconds

def seconds_to_time(total_seconds):
    """Convert total seconds to 'mm:ss' format"""
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def extract_inning_examples(sound_duration=2.0, padding=0.5):
    """
    Extract all inning transition examples and analyze their characteristics.
    
    Args:
        sound_duration (float): Expected duration of each inning sound in seconds
        padding (float): Extra time to include for context
    """
    print("=" * 60)
    print("BUILDING INNING TRANSITION REFERENCE LIBRARY")
    print("=" * 60)
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    output_dir = Path("reference_sounds")
    output_dir.mkdir(exist_ok=True)
    
    # Storage for all extracted examples
    all_examples = []
    sample_rates = []
    
    print(f"Extracting {len(inning_transitions)} inning transition examples...")
    print(f"Each example: {sound_duration}s duration with {padding}s padding")
    
    for i, transition in enumerate(inning_transitions):
        inning_num = transition["inning"]
        time_str = transition["time_mm_ss"]
        start_time = transition["time_seconds"]
        end_time = start_time + sound_duration
        
        print(f"\nExample {i+1}: Inning {inning_num} at {time_str}")
        print(f"  Extracting from {start_time}s to {end_time}s")
        
        try:
            # Load the specific segment with padding
            audio_data, sample_rate = librosa.load(
                audio_file,
                sr=22050,
                offset=max(0, start_time - padding),
                duration=sound_duration + (2 * padding)
            )
            
            # Calculate the exact segment within the loaded audio
            if start_time >= padding:
                segment_start = int(padding * sample_rate)
            else:
                segment_start = int(start_time * sample_rate)
                
            segment_end = segment_start + int(sound_duration * sample_rate)
            
            # Extract the exact inning sound
            inning_sound = audio_data[segment_start:segment_end]
            
            # Save individual example
            filename = f"inning_example_{i+1}_inning{inning_num}_{time_str.replace(':', '-')}.wav"
            output_path = output_dir / filename
            sf.write(str(output_path), inning_sound, sample_rate)
            
            # Analyze characteristics
            peak_amp = np.max(np.abs(inning_sound))
            rms_amp = np.sqrt(np.mean(inning_sound**2))
            
            print(f"  [SAVED] {filename}")
            print(f"  Duration: {len(inning_sound)/sample_rate:.3f}s")
            print(f"  Peak: {peak_amp:.4f}, RMS: {rms_amp:.4f}")
            print(f"  Samples: {len(inning_sound):,}")
            
            # Store for analysis
            all_examples.append(inning_sound)
            sample_rates.append(sample_rate)
            
        except Exception as e:
            print(f"  [ERROR] Failed to extract example {i+1}: {str(e)}")
    
    # Analyze all examples together
    if all_examples:
        print(f"\n{'='*60}")
        print("REFERENCE LIBRARY ANALYSIS")
        print(f"{'='*60}")
        
        print(f"Successfully extracted: {len(all_examples)}/{len(inning_transitions)} examples")
        
        # Calculate statistics across all examples
        all_peaks = [np.max(np.abs(ex)) for ex in all_examples]
        all_rms = [np.sqrt(np.mean(ex**2)) for ex in all_examples]
        all_durations = [len(ex)/sr for ex, sr in zip(all_examples, sample_rates)]
        
        print(f"\nCHARACTERISTICS ACROSS ALL EXAMPLES:")
        print(f"Duration - Mean: {np.mean(all_durations):.3f}s, Std: {np.std(all_durations):.3f}s")
        print(f"Peak Amp - Mean: {np.mean(all_peaks):.4f}, Std: {np.std(all_peaks):.4f}")
        print(f"RMS Amp  - Mean: {np.mean(all_rms):.4f}, Std: {np.std(all_rms):.4f}")
        
        # Create average reference pattern
        if len(set(sample_rates)) == 1:  # All same sample rate
            # Ensure all examples are same length
            min_length = min(len(ex) for ex in all_examples)
            trimmed_examples = [ex[:min_length] for ex in all_examples]
            
            # Calculate average pattern
            average_pattern = np.mean(trimmed_examples, axis=0)
            
            # Save average pattern
            avg_filename = output_dir / "inning_transition_average_pattern.wav"
            sf.write(str(avg_filename), average_pattern, sample_rates[0])
            
            print(f"\n[SAVED] Average pattern: {avg_filename}")
            print(f"        This is our master reference for pattern matching!")
            print(f"        Length: {len(average_pattern):,} samples ({len(average_pattern)/sample_rates[0]:.3f}s)")
            
            return all_examples, average_pattern, sample_rates[0]
        else:
            print("Warning: Sample rates don't match, can't create average pattern")
            return all_examples, None, None
    
    else:
        print("No examples successfully extracted!")
        return [], None, None

def test_conversions():
    """Test the time conversion functions with our data"""
    print("Testing time conversions:")
    for transition in inning_transitions:
        original = transition["time_mm_ss"]
        calculated = seconds_to_time(transition["time_seconds"])
        recalculated = time_to_seconds(calculated)
        print(f"Inning {transition['inning']}: {original} -> {transition['time_seconds']}s -> {calculated} -> {recalculated}s")

if __name__ == "__main__":
    # Test conversions first
    test_conversions()
    print()
    
    # Extract all examples
    examples, avg_pattern, sample_rate = extract_inning_examples()
    
    if examples:
        print(f"\n{'='*60}")
        print("SUCCESS! Inning transition reference library built!")
        print("Ready for automated pattern matching development.")
        print(f"{'='*60}")
    else:
        print("Failed to build reference library")