"""
Download official Mario Superstar Baseball game audio tracks
from KHInsider to get clean reference patterns.
"""

import requests
import os
from pathlib import Path
import time

def download_khinsider_track(track_url, output_file):
    """
    Download a specific track from KHInsider.
    
    Args:
        track_url (str): Direct URL to the MP3 file
        output_file (str): Output filename
    """
    try:
        print(f"Downloading: {output_file}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(track_url, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"[SUCCESS] Downloaded: {output_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to download {output_file}: {e}")
        return False

def download_mario_baseball_audio():
    """
    Download the key audio tracks we need for inning transition detection.
    """
    print("Downloading Official Mario Superstar Baseball Audio")
    print("=" * 55)
    
    output_dir = Path("official_game_audio")
    output_dir.mkdir(exist_ok=True)
    
    # Key tracks we want to download
    # Note: These URLs are examples - you'll need to get the actual direct links
    target_tracks = [
        {
            "name": "Next Inning",
            "filename": "27_next_inning.mp3",
            "description": "Most likely inning transition sound"
        },
        {
            "name": "Batter Up!",
            "filename": "20_batter_up.mp3", 
            "description": "Possible start-of-inning sound"
        },
        {
            "name": "Superstar Matchup",
            "filename": "18_superstar_matchup.mp3",
            "description": "Possible transition sound"
        },
        {
            "name": "That's the Game!",
            "filename": "28_thats_the_game.mp3",
            "description": "End of game sound"
        }
    ]
    
    print("Target tracks to download:")
    for i, track in enumerate(target_tracks, 1):
        print(f"  {i}. {track['name']} - {track['description']}")
    
    print(f"\nNOTE: Manual download required!")
    print(f"Please visit: https://downloads.khinsider.com/game-soundtracks/album/mario-superstar-baseball-gamecube-ost")
    print(f"And download these specific tracks to the '{output_dir}' folder:")
    
    for track in target_tracks:
        print(f"  - Track: '{track['name']}' -> Save as: {track['filename']}")
    
    print(f"\nOnce downloaded, run the next script to convert and analyze them.")
    
    return output_dir

def check_downloaded_files():
    """
    Check which files have been manually downloaded.
    """
    output_dir = Path("official_game_audio")
    
    if not output_dir.exists():
        print("No official_game_audio directory found")
        return []
    
    downloaded_files = list(output_dir.glob("*.mp3"))
    
    print(f"Found {len(downloaded_files)} downloaded audio files:")
    for file in downloaded_files:
        file_size = file.stat().st_size / 1024  # KB
        print(f"  - {file.name} ({file_size:.1f} KB)")
    
    return downloaded_files

if __name__ == "__main__":
    # First, set up the download instructions
    download_mario_baseball_audio()
    
    print(f"\n" + "="*55)
    print("NEXT STEPS:")
    print("1. Manually download the tracks from KHInsider")
    print("2. Run this script again to check downloaded files")
    print("3. Convert MP3s to WAV for audio analysis")
    print("4. Test pattern matching with clean game audio")
    
    # Check if any files are already downloaded
    print(f"\nChecking for existing downloads...")
    downloaded = check_downloaded_files()
    
    if downloaded:
        print(f"\nSome files already downloaded! Ready for conversion.")
    else:
        print(f"\nNo files found yet. Please download manually first.")