"""
Multi-Template Inning Chime Detection System

Uses multiple clean chime samples to create a robust detection system.
Combines user-extracted samples with official audio for best results.
"""

import librosa
import numpy as np
from scipy import signal
from pathlib import Path
from audio_filtering import AudioFilter
import soundfile as sf

class MultiTemplateDetector:
    def __init__(self):
        self.sample_rate = 22050
        self.audio_filter = AudioFilter()
        self.chime_templates = []
        self.template_names = []
        
    def load_chime_templates(self):
        """
        Load all chime templates from better_samples + official sample.
        """
        print("LOADING CHIME TEMPLATES")
        print("=" * 40)
        
        template_files = [
            ("better_samples/chime_sample_01.wav", "User Sample 01"),
            ("better_samples/chime_sample_02.wav", "User Sample 02"), 
            ("better_samples/chime_sample_03.wav", "User Sample 03"),
            ("better_samples/chime_sample_04.wav", "User Sample 04"),
            ("better_samples/chime_sample_05.wav", "User Sample 05"),
            ("better_samples/chime_sample_06.wav", "User Sample 06 (18:39)"),
            ("reference_sounds/official_inning_transition_pattern.wav", "Official Sample")
        ]
        
        templates_loaded = 0
        
        for file_path, name in template_files:
            try:
                audio, sr = librosa.load(file_path, sr=self.sample_rate)
                
                # Normalize template
                audio_normalized = audio / np.max(np.abs(audio))
                
                self.chime_templates.append(audio_normalized)
                self.template_names.append(name)
                
                duration = len(audio) / sr
                rms = np.sqrt(np.mean(audio**2))
                
                print(f"[OK] {name}: {duration:.2f}s, RMS: {rms:.4f}")
                templates_loaded += 1
                
            except Exception as e:
                print(f"[ERROR] {name}: ERROR - {e}")
        
        print(f"\nLoaded {templates_loaded} chime templates successfully")
        return templates_loaded > 0
    
    def analyze_template_characteristics(self):
        """
        Analyze the characteristics of all loaded templates.
        """
        print(f"\nTEMPLATE ANALYSIS")
        print("-" * 30)
        
        if not self.chime_templates:
            print("No templates loaded!")
            return
        
        durations = []
        rms_values = []
        
        for i, (template, name) in enumerate(zip(self.chime_templates, self.template_names)):
            duration = len(template) / self.sample_rate
            rms = np.sqrt(np.mean(template**2))
            
            durations.append(duration)
            rms_values.append(rms)
            
            print(f"{i+1}. {name}: {duration:.2f}s, RMS: {rms:.4f}")
        
        print(f"\nStatistics:")
        print(f"Duration range: {min(durations):.2f}s to {max(durations):.2f}s")
        print(f"Average duration: {np.mean(durations):.2f}s")
        print(f"RMS range: {min(rms_values):.4f} to {max(rms_values):.4f}")
        
        return durations, rms_values
    
    def detect_with_multiple_templates(self, video_file, max_duration=None):
        """
        Detect inning transitions using all templates and combine results.
        """
        print(f"\nMULTI-TEMPLATE DETECTION")
        print("=" * 50)
        
        # Load video audio
        try:
            print("Loading video audio...")
            if max_duration:
                audio_data, sr = librosa.load(video_file, sr=self.sample_rate, duration=max_duration)
                print(f"Loaded: {max_duration/60:.1f} minutes")
            else:
                audio_data, sr = librosa.load(video_file, sr=self.sample_rate)
                duration_minutes = len(audio_data) / sr / 60
                print(f"Loaded: {duration_minutes:.1f} minutes")
            
        except Exception as e:
            print(f"ERROR loading audio: {e}")
            return []
        
        # Apply frequency filtering
        print("Applying frequency band filtering...")
        filtered_audio = self.audio_filter.frequency_band_filter(audio_data)
        audio_normalized = filtered_audio / np.max(np.abs(filtered_audio))
        
        # Test each template
        all_detections = {}
        correlation_stats = {}
        
        print(f"\nTesting {len(self.chime_templates)} templates:")
        
        for i, (template, name) in enumerate(zip(self.chime_templates, self.template_names)):
            print(f"\n{i+1}. {name}:")
            
            # Cross-correlation
            correlation = signal.correlate(audio_normalized, template, mode='valid')
            correlation = correlation / len(template)
            
            # Statistics
            corr_min, corr_max = np.min(correlation), np.max(correlation)
            corr_mean, corr_std = np.mean(correlation), np.std(correlation)
            
            print(f"   Correlation range: {corr_min:.6f} to {corr_max:.6f}")
            print(f"   Mean: {corr_mean:.6f}, Std: {corr_std:.6f}")
            
            correlation_stats[name] = {
                'min': corr_min, 'max': corr_max, 
                'mean': corr_mean, 'std': corr_std,
                'correlation': correlation
            }
            
            # Find peaks with conservative threshold
            threshold = np.percentile(correlation, 99.7)  # Very conservative
            min_gap_samples = int(60 * sr)  # 1 minute minimum
            
            peak_indices, _ = signal.find_peaks(
                correlation, 
                height=threshold, 
                distance=min_gap_samples
            )
            
            # Convert to detections
            detections = []
            for idx in peak_indices:
                time_sec = idx / sr
                score = correlation[idx]
                detections.append((time_sec, score))
            
            all_detections[name] = detections
            print(f"   Found {len(detections)} detections with threshold {threshold:.6f}")
        
        return all_detections, correlation_stats
    
    def combine_template_results(self, all_detections, tolerance=5.0):
        """
        Combine results from multiple templates using consensus voting.
        """
        print(f"\nCOMBINING TEMPLATE RESULTS")
        print("-" * 40)
        
        # Collect all unique detection times
        all_times = []
        for template_name, detections in all_detections.items():
            for time_sec, score in detections:
                all_times.append((time_sec, template_name, score))
        
        # Sort by time
        all_times.sort(key=lambda x: x[0])
        
        # Group nearby detections (within tolerance)
        consensus_detections = []
        i = 0
        
        while i < len(all_times):
            current_time, current_template, current_score = all_times[i]
            
            # Find all detections within tolerance of current time
            group = [(current_time, current_template, current_score)]
            j = i + 1
            
            while j < len(all_times):
                next_time, next_template, next_score = all_times[j]
                if abs(next_time - current_time) <= tolerance:
                    group.append((next_time, next_template, next_score))
                    j += 1
                else:
                    break
            
            # If multiple templates agree, this is a strong detection
            if len(group) >= 2:  # At least 2 templates must agree
                # Use the detection with highest score as representative
                best_detection = max(group, key=lambda x: x[2])
                consensus_time, _, consensus_score = best_detection
                
                # Calculate consensus strength (how many templates agreed)
                consensus_strength = len(group)
                template_names = [t[1] for t in group]
                
                consensus_detections.append({
                    'time': consensus_time,
                    'score': consensus_score,
                    'strength': consensus_strength,
                    'templates': template_names
                })
                
                mm, ss = int(consensus_time // 60), int(consensus_time % 60)
                print(f"Consensus: {mm}:{ss:02d} ({consensus_time:.1f}s) - "
                      f"Strength: {consensus_strength}/{len(self.chime_templates)} - "
                      f"Score: {consensus_score:.6f}")
            
            i = j if j > i + 1 else i + 1
        
        print(f"\nFound {len(consensus_detections)} consensus detections")
        
        # Sort by consensus strength then score
        consensus_detections.sort(key=lambda x: (x['strength'], x['score']), reverse=True)
        
        return consensus_detections
    
    def validate_detections(self, consensus_detections, known_transitions):
        """
        Validate consensus detections against known transitions.
        """
        print(f"\nVALIDATION AGAINST KNOWN TRANSITIONS")
        print("-" * 50)
        
        if not consensus_detections:
            print("No detections to validate!")
            return 0.0
        
        found_count = 0
        tolerance = 10.0  # 10 second tolerance
        
        for expected in known_transitions:
            mm_exp, ss_exp = int(expected // 60), int(expected % 60)
            
            # Find closest consensus detection
            matches = [
                det for det in consensus_detections 
                if abs(det['time'] - expected) <= tolerance
            ]
            
            if matches:
                # Use the strongest consensus match
                best_match = max(matches, key=lambda x: x['strength'])
                match_time = best_match['time']
                match_strength = best_match['strength']
                match_score = best_match['score']
                
                mm_match, ss_match = int(match_time // 60), int(match_time % 60)
                error = abs(match_time - expected)
                
                print(f"[FOUND] {mm_exp}:{ss_exp:02d} -> {mm_match}:{ss_match:02d} "
                      f"(error: {error:.1f}s, strength: {match_strength}/{len(self.chime_templates)}, "
                      f"score: {match_score:.6f})")
                found_count += 1
            else:
                print(f"[MISSED] {mm_exp}:{ss_exp:02d} -> No consensus detection within {tolerance}s")
        
        accuracy = found_count / len(known_transitions)
        print(f"\nAccuracy: {accuracy:.1%} ({found_count}/{len(known_transitions)} found)")
        
        return accuracy

def test_multi_template_system():
    """
    Test the multi-template detection system.
    """
    print("MULTI-TEMPLATE INNING CHIME DETECTION SYSTEM")
    print("=" * 70)
    
    detector = MultiTemplateDetector()
    
    # Load templates
    if not detector.load_chime_templates():
        print("Failed to load templates!")
        return
    
    # Analyze template characteristics
    detector.analyze_template_characteristics()
    
    # Test on original video
    video_file = "temp_audio/The CRAZIEST hit in Mario Baseball.webm"
    known_transitions = [148, 199, 243, 314, 454, 1119, 1174]  # Include 9th inning
    
    print(f"\nTesting on: {Path(video_file).name}")
    print(f"Known transitions: {len(known_transitions)}")
    
    # Run detection with all templates
    all_detections, correlation_stats = detector.detect_with_multiple_templates(video_file)
    
    # Show individual template results
    print(f"\nINDIVIDUAL TEMPLATE RESULTS:")
    for template_name, detections in all_detections.items():
        print(f"{template_name}: {len(detections)} detections")
    
    # Combine results using consensus
    consensus_detections = detector.combine_template_results(all_detections)
    
    # Validate against known transitions
    accuracy = detector.validate_detections(consensus_detections, known_transitions)
    
    print(f"\n" + "=" * 70)
    print("FINAL RESULTS:")
    print(f"Templates used: {len(detector.chime_templates)}")
    print(f"Consensus detections: {len(consensus_detections)}")
    print(f"Accuracy: {accuracy:.1%}")
    
    if accuracy >= 0.9:
        print("[EXCELLENT] Ready for production!")
    elif accuracy >= 0.8:
        print("[VERY GOOD] Minor tuning may help")
    elif accuracy >= 0.6:
        print("[GOOD] Needs some improvement")
    else:
        print("[NEEDS WORK] Consider more templates or different approach")
    
    return consensus_detections, accuracy

if __name__ == "__main__":
    test_multi_template_system()