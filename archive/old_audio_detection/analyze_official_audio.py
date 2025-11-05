"""
Analyze the official Mario Superstar Baseball audio tracks
to find the correct inning transition sound and build a clean reference pattern.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
import glob

def analyze_official_audio():
    """
    Analyze all downloaded official game audio tracks.
    """
    print("Analyzing Official Mario Superstar Baseball Audio")
    print("=" * 55)
    
    # Find all MP3 files in the official_game_audio directory
    audio_dir = Path("official_game_audio")
    mp3_files = list(audio_dir.glob("*.mp3"))
    
    if not mp3_files:
        print("No MP3 files found in official_game_audio directory!")
        return
    
    print(f"Found {len(mp3_files)} official audio tracks:")
    for file in mp3_files:
        print(f"  - {file.name}")
    
    # Create output directory for converted WAV files
    wav_dir = Path("official_audio_wav")
    wav_dir.mkdir(exist_ok=True)
    
    playback_dir = Path("official_audio_playback")
    playback_dir.mkdir(exist_ok=True)
    
    print(f"\n1. CONVERTING AND ANALYZING EACH TRACK:")
    print("-" * 45)
    
    analyzed_tracks = []
    
    for mp3_file in mp3_files:
        print(f"\nAnalyzing: {mp3_file.name}")
        
        try:
            # Load the MP3 file
            audio_data, sample_rate = librosa.load(str(mp3_file), sr=22050)
            duration = len(audio_data) / sample_rate
            
            print(f"  Duration: {duration:.2f} seconds")
            print(f"  Sample rate: {sample_rate:,} Hz")
            print(f"  Samples: {len(audio_data):,}")
            
            # Analyze audio characteristics
            rms = np.sqrt(np.mean(audio_data**2))
            peak = np.max(np.abs(audio_data))
            
            print(f"  RMS amplitude: {rms:.4f}")
            print(f"  Peak amplitude: {peak:.4f}")
            
            # Save as WAV for better compatibility
            wav_filename = mp3_file.stem + ".wav"
            wav_path = wav_dir / wav_filename
            sf.write(str(wav_path), audio_data, sample_rate)
            
            # Also save a copy for easy playback verification
            playback_path = playback_dir / wav_filename
            sf.write(str(playback_path), audio_data, sample_rate)
            
            print(f"  [SAVED] {wav_filename}")
            
            # Store analysis results
            analyzed_tracks.append({
                'name': mp3_file.stem,
                'file': str(wav_path),
                'playback_file': str(playback_path),
                'duration': duration,
                'rms': rms,
                'peak': peak,
                'audio_data': audio_data,
                'sample_rate': sample_rate
            })
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {mp3_file.name}: {e}")
    
    # Identify the most likely inning transition sound
    print(f"\n2. IDENTIFYING BEST INNING TRANSITION CANDIDATE:")
    print("-" * 50)
    
    # "Next Inning" is our prime suspect
    next_inning_track = None
    for track in analyzed_tracks:
        if "next inning" in track['name'].lower():
            next_inning_track = track
            break
    
    if next_inning_track:
        print(f"Found 'Next Inning' track - this is most likely our target!")
        print(f"  File: {next_inning_track['name']}")
        print(f"  Duration: {next_inning_track['duration']:.2f}s")
        print(f"  RMS: {next_inning_track['rms']:.4f}")
        
        # Save this as our new reference pattern
        reference_dir = Path("reference_sounds")
        reference_dir.mkdir(exist_ok=True)
        
        official_reference = reference_dir / "official_inning_transition_pattern.wav"
        sf.write(str(official_reference), next_inning_track['audio_data'], next_inning_track['sample_rate'])
        
        print(f"  [SAVED] New reference pattern: {official_reference}")
        
        # Compare with our old reference
        try:
            old_reference, _ = librosa.load("reference_sounds/refined_inning_transition_pattern.wav", sr=22050)
            
            if len(old_reference) == len(next_inning_track['audio_data']):
                correlation = np.corrcoef(old_reference, next_inning_track['audio_data'])[0, 1]
                print(f"  Similarity to old pattern: {correlation:.4f}")
            else:
                print(f"  Old pattern length: {len(old_reference)}, New: {len(next_inning_track['audio_data'])}")
                
        except Exception as e:
            print(f"  Could not compare with old pattern: {e}")
        
        recommended_file = next_inning_track
    else:
        print("No 'Next Inning' track found. Analyzing all tracks...")
        
        # Find the shortest track (likely to be a sound effect)
        shortest_track = min(analyzed_tracks, key=lambda x: x['duration'])
        print(f"Shortest track (likely sound effect): {shortest_track['name']} ({shortest_track['duration']:.2f}s)")
        recommended_file = shortest_track
    
    # Show all tracks for comparison
    print(f"\n3. ALL TRACKS SUMMARY:")
    print("-" * 30)
    for track in sorted(analyzed_tracks, key=lambda x: x['duration']):
        duration_str = f"{track['duration']:.2f}s"
        print(f"  {track['name']:<25} {duration_str:>8} (RMS: {track['rms']:.4f})")
    
    # Instructions for verification
    print(f"\n4. VERIFICATION INSTRUCTIONS:")
    print("-" * 35)
    print(f"Audio files for playback saved to: {playback_dir}")
    print(f"")
    print(f"Please listen to these files to verify which sounds like inning transitions:")
    
    for track in analyzed_tracks:
        playback_file = Path(track['playback_file']).name
        print(f"  - {playback_file:<35} ({track['duration']:.1f}s)")
    
    print(f"")
    print(f"RECOMMENDED: Listen to '{Path(recommended_file['playback_file']).name}' first!")
    print(f"This is most likely to be the inning transition sound.")
    
    print(f"\n5. NEXT STEPS:")
    print("-" * 15)
    if next_inning_track:
        print(f"If 'Next Inning' sounds correct:")
        print(f"  - We'll use it as our new reference pattern")
        print(f"  - Test pattern matching on both videos")
        print(f"  - Should get much better accuracy!")
    
    print(f"If a different track sounds right:")
    print(f"  - Tell me which one")
    print(f"  - I'll use that as the reference instead")
    
    return analyzed_tracks, recommended_file

if __name__ == "__main__":
    tracks, recommended = analyze_official_audio()
    
    if tracks:
        print(f"\n{'='*55}")
        print(f"SUCCESS! Official audio tracks analyzed and converted.")
        print(f"Ready for verification and pattern matching!")
        print(f"{'='*55}")
    else:
        print("Failed to analyze official audio tracks")