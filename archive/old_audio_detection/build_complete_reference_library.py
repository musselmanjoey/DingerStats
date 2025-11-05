"""
Build Complete Reference Library with All 5 Inning Transitions

Extract all 5 inning transition examples and create an improved 
reference pattern for much better pattern matching accuracy.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

def build_complete_reference():
    """
    Extract all 5 inning transition examples and build improved reference pattern.
    """
    print("=" * 60)
    print("BUILDING COMPLETE INNING TRANSITION REFERENCE LIBRARY")
    print("=" * 60)
    print("Extracting all 5 inning transitions for improved pattern matching")
    
    # All 5 inning transitions with corrected timestamps
    inning_transitions = [
        {"inning": "1st-top-to-bottom", "time_mm_ss": "2:28", "time_seconds": 2*60 + 28},
        {"inning": "1st-bottom-to-2nd-top", "time_mm_ss": "3:19", "time_seconds": 3*60 + 19}, 
        {"inning": "2nd-top-to-bottom", "time_mm_ss": "4:03", "time_seconds": 4*60 + 3},
        {"inning": "2nd-bottom-to-3rd-top", "time_mm_ss": "5:14", "time_seconds": 5*60 + 14},
        {"inning": "3rd-top-to-bottom", "time_mm_ss": "7:34", "time_seconds": 7*60 + 34},
    ]
    
    audio_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    output_dir = Path("reference_sounds")
    output_dir.mkdir(exist_ok=True)
    
    # Storage for all extracted examples
    all_examples = []
    sound_duration = 2.0  # 2 seconds per transition
    padding = 0.5  # 0.5 second padding
    
    print(f"Extracting {len(inning_transitions)} inning transition examples...")
    print(f"Each example: {sound_duration}s duration with {padding}s padding")
    
    for i, transition in enumerate(inning_transitions):
        inning_desc = transition["inning"]
        time_str = transition["time_mm_ss"] 
        start_time = transition["time_seconds"]
        end_time = start_time + sound_duration
        
        print(f"\nExample {i+1}: {inning_desc} at {time_str}")
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
            safe_desc = inning_desc.replace("-", "_")
            filename = f"complete_example_{i+1}_{safe_desc}_{time_str.replace(':', '-')}.wav"
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
            
        except Exception as e:
            print(f"  [ERROR] Failed to extract example {i+1}: {str(e)}")
    
    # Analyze all examples together
    if all_examples:
        print(f"\n{'='*60}")
        print("COMPLETE REFERENCE LIBRARY ANALYSIS") 
        print(f"{'='*60}")
        
        print(f"Successfully extracted: {len(all_examples)}/{len(inning_transitions)} examples")
        
        # Calculate statistics across all examples
        all_peaks = [np.max(np.abs(ex)) for ex in all_examples]
        all_rms = [np.sqrt(np.mean(ex**2)) for ex in all_examples]
        all_durations = [len(ex)/22050 for ex in all_examples]  # Using known sample rate
        
        print(f"\nCHARACTERISTICS ACROSS ALL 5 EXAMPLES:")
        print(f"Duration - Mean: {np.mean(all_durations):.3f}s, Std: {np.std(all_durations):.3f}s")
        print(f"Peak Amp - Mean: {np.mean(all_peaks):.4f}, Std: {np.std(all_peaks):.4f}")
        print(f"RMS Amp  - Mean: {np.mean(all_rms):.4f}, Std: {np.std(all_rms):.4f}")
        
        # Create improved average reference pattern
        # Ensure all examples are same length
        min_length = min(len(ex) for ex in all_examples)
        trimmed_examples = [ex[:min_length] for ex in all_examples]
        
        # Calculate average pattern
        average_pattern = np.mean(trimmed_examples, axis=0)
        
        # Save improved average pattern
        avg_filename = output_dir / "improved_inning_transition_pattern.wav"
        sf.write(str(avg_filename), average_pattern, 22050)
        
        print(f"\n[SAVED] Improved average pattern: {avg_filename}")
        print(f"        Based on all 5 examples instead of just 3!")
        print(f"        Length: {len(average_pattern):,} samples ({len(average_pattern)/22050:.3f}s)")
        
        # Create individual correlation templates (for debugging)
        print(f"\nCreating individual correlation templates...")
        correlations_dir = output_dir / "individual_templates"
        correlations_dir.mkdir(exist_ok=True)
        
        for i, example in enumerate(all_examples):
            template_name = f"template_{i+1}_{inning_transitions[i]['time_mm_ss'].replace(':', '-')}.wav"
            template_path = correlations_dir / template_name
            sf.write(str(template_path), example, 22050)
        
        print(f"[SAVED] {len(all_examples)} individual templates in: {correlations_dir}")
        
        # Show comparison with original (3-example) pattern
        try:
            old_pattern, _ = librosa.load("reference_sounds/inning_transition_average_pattern.wav", sr=22050)
            
            print(f"\nCOMPARISON WITH ORIGINAL PATTERN:")
            print(f"Original (3 examples): {len(old_pattern):,} samples, RMS: {np.sqrt(np.mean(old_pattern**2)):.4f}")
            print(f"Improved (5 examples): {len(average_pattern):,} samples, RMS: {np.sqrt(np.mean(average_pattern**2)):.4f}")
            
            # Cross-correlation between old and new patterns
            if len(old_pattern) == len(average_pattern):
                correlation = np.corrcoef(old_pattern, average_pattern)[0, 1]
                print(f"Similarity between patterns: {correlation:.4f}")
            
        except:
            print("Could not load original pattern for comparison")
        
        return all_examples, average_pattern, inning_transitions
    
    else:
        print("No examples successfully extracted!")
        return [], None, []

if __name__ == "__main__":
    examples, improved_pattern, transitions = build_complete_reference()
    
    if examples:
        print(f"\n{'='*60}")
        print("SUCCESS! Complete inning transition reference library built!")
        print("Ready for improved automated pattern matching.")
        print(f"With {len(examples)} examples, accuracy should be much higher!")
        print(f"{'='*60}")
    else:
        print("Failed to build complete reference library")