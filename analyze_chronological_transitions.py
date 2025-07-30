"""
Analyze the detected transitions in chronological order to identify
the most likely 9 inning transitions based on realistic timing patterns.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path

def analyze_chronological_transitions():
    """
    Analyze transitions chronologically and apply baseball game logic.
    """
    print("Chronological Inning Transition Analysis")
    print("=" * 45)
    
    # Load everything we need
    temp_dir = Path("temp_audio_new")
    audio_files = list(temp_dir.glob("*.webm"))
    audio_file = str(audio_files[0])
    
    pattern_file = "reference_sounds/refined_inning_transition_pattern.wav"
    reference_pattern, ref_sr = librosa.load(pattern_file, sr=22050)
    audio_data, audio_sr = librosa.load(audio_file, sr=22050, duration=1800)  # 30 minutes
    
    print(f"Analyzing {len(audio_data)/audio_sr/60:.1f} minutes of audio")
    
    # Compute correlation
    ref_normalized = reference_pattern / np.max(np.abs(reference_pattern))
    audio_normalized = audio_data / np.max(np.abs(audio_data))
    correlation = signal.correlate(audio_normalized, ref_normalized, mode='valid')
    correlation = correlation / len(ref_normalized)
    
    # Use a moderately selective threshold
    threshold = np.percentile(correlation, 99.7)  # Between our tested values
    min_gap_samples = int(60 * audio_sr)  # 1 minute minimum gap
    
    peaks, _ = signal.find_peaks(correlation, height=threshold, distance=min_gap_samples)
    
    # Convert to times and sort chronologically
    all_matches = []
    for idx in peaks:
        time_sec = idx / audio_sr
        score = correlation[idx]
        all_matches.append((time_sec, score))
    
    # Sort by TIME (not score) for chronological analysis
    all_matches.sort(key=lambda x: x[0])  # Sort by time
    
    print(f"\n1. ALL DETECTIONS IN CHRONOLOGICAL ORDER:")
    print(f"   Threshold: {threshold:.6f} ({len(all_matches)} total detections)")
    
    for i, (time, score) in enumerate(all_matches):
        mm = int(time // 60)
        ss = int(time % 60)
        print(f"   {i+1:2d}: {mm:2d}:{ss:02d} ({time:6.1f}s) - Score: {score:.6f}")
    
    # Apply baseball game logic to filter the most likely 9 transitions
    print(f"\n2. APPLYING BASEBALL GAME LOGIC:")
    
    if len(all_matches) >= 9:
        # Method 1: Take every N-th detection to spread across game
        step = len(all_matches) / 9
        selected_indices = [int(i * step) for i in range(9)]
        method1_matches = [all_matches[i] for i in selected_indices]
        
        print(f"   Method 1 - Evenly spaced across game:")
        for i, (time, score) in enumerate(method1_matches):
            mm = int(time // 60)
            ss = int(time % 60)
            print(f"     Inning {i+1}: {mm:2d}:{ss:02d} - Score: {score:.6f}")
        
        # Method 2: Filter by minimum realistic spacing (2+ minutes between innings)
        method2_matches = []
        last_time = -120  # Start 2 minutes before zero
        
        for time, score in all_matches:
            if time - last_time >= 120:  # At least 2 minutes gap
                method2_matches.append((time, score))
                last_time = time
                if len(method2_matches) >= 9:  # Stop at 9 innings
                    break
        
        print(f"\n   Method 2 - Realistic spacing (2+ min gaps):")
        for i, (time, score) in enumerate(method2_matches):
            mm = int(time // 60)
            ss = int(time % 60)
            print(f"     Inning {i+1}: {mm:2d}:{ss:02d} - Score: {score:.6f}")
        
        # Method 3: Take top 9 by correlation score
        top_9_by_score = sorted(all_matches, key=lambda x: x[1], reverse=True)[:9]
        top_9_by_score.sort(key=lambda x: x[0])  # Re-sort by time for display
        
        print(f"\n   Method 3 - Top 9 correlation scores (chronological):")
        for i, (time, score) in enumerate(top_9_by_score):
            mm = int(time // 60)
            ss = int(time % 60)
            print(f"     Inning {i+1}: {mm:2d}:{ss:02d} - Score: {score:.6f}")
        
        # Recommend the best method
        print(f"\n3. RECOMMENDATION:")
        
        # Check which method has most realistic timing
        methods = [
            ("Evenly Spaced", method1_matches),
            ("Realistic Spacing", method2_matches), 
            ("Top Scores", top_9_by_score)
        ]
        
        best_method = None
        best_score = -1
        
        for method_name, matches in methods:
            if len(matches) >= 2:
                times = [t for t, s in matches]
                gaps = [times[i+1] - times[i] for i in range(len(times)-1)]
                avg_gap = np.mean(gaps)
                gap_consistency = 1 / (np.std(gaps) + 1)  # Higher is better
                
                # Score based on realistic average (3-4 min ideal) and consistency
                ideal_gap = 200  # ~3.3 minutes per inning
                gap_score = 1 / (abs(avg_gap - ideal_gap) + 1)
                total_score = gap_score * gap_consistency
                
                print(f"   {method_name}: Avg gap {avg_gap:.1f}s, Score: {total_score:.3f}")
                
                if total_score > best_score:
                    best_score = total_score
                    best_method = (method_name, matches)
        
        if best_method:
            name, final_matches = best_method
            print(f"\n   RECOMMENDED: {name}")
            print(f"   These {len(final_matches)} timestamps are most likely inning transitions:")
            
            for i, (time, score) in enumerate(final_matches):
                mm = int(time // 60)
                ss = int(time % 60)
                print(f"     {i+1}. {mm:2d}:{ss:02d}")
            
            print(f"\n   MANUAL VERIFICATION NEEDED:")
            print(f"   Please check these timestamps in the YouTube video:")
            sample_times = final_matches[:3]  # First 3 for verification
            for i, (time, score) in enumerate(sample_times):
                mm = int(time // 60)
                ss = int(time % 60)
                print(f"   - Check {mm:2d}:{ss:02d} for inning transition sound/visual")
            
            return final_matches
    
    else:
        print(f"   Only found {len(all_matches)} transitions - need to lower threshold")
        return all_matches

if __name__ == "__main__":
    analyze_chronological_transitions()