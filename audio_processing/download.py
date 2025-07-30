"""
Audio Download Module for Mario Baseball Stats Tracking

This module handles downloading audio from Dinger City YouTube videos
using yt-dlp. It extracts only the audio track to save bandwidth and storage.
"""

import os
import yt_dlp
from pathlib import Path


class AudioDownloader:
    def __init__(self, output_dir="temp_audio"):
        """
        Initialize the audio downloader.
        
        Args:
            output_dir (str): Directory to save downloaded audio files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # yt-dlp options optimized for audio extraction
        self.ydl_opts = {
            'format': 'bestaudio/best',  # Download best audio quality
            'outtmpl': str(self.output_dir / '%(title)s.%(ext)s'),
            'extractaudio': True,
            'audioformat': 'wav',  # Convert to WAV for librosa compatibility
            'audioquality': '192K',  # Good quality for audio analysis
            'noplaylist': True,  # Only download single video, not playlist
            'quiet': False,  # Set to True to suppress output
        }
    
    def download_audio(self, video_url):
        """
        Download audio from a YouTube video URL.
        
        Args:
            video_url (str): YouTube video URL
            
        Returns:
            str: Path to the downloaded audio file, or None if failed
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video info first
                info = ydl.extract_info(video_url, download=False)
                video_title = info.get('title', 'Unknown')
                print(f"Downloading audio from: {video_title}")
                
                # Download the audio
                ydl.download([video_url])
                
                # Find the downloaded file
                audio_file = self._find_downloaded_file(video_title)
                if audio_file:
                    print(f"Successfully downloaded: {audio_file}")
                    return str(audio_file)
                else:
                    print("Error: Could not locate downloaded file")
                    return None
                    
        except Exception as e:
            print(f"Error downloading audio: {str(e)}")
            return None
    
    def _find_downloaded_file(self, video_title):
        """
        Find the downloaded audio file based on video title.
        
        Args:
            video_title (str): Title of the video
            
        Returns:
            Path: Path to the audio file, or None if not found
        """
        # yt-dlp might change the filename, so search for files with similar names
        for file_path in self.output_dir.iterdir():
            if file_path.is_file() and video_title.split()[0] in file_path.name:
                return file_path
        
        # If exact match not found, return the most recent file
        audio_files = [f for f in self.output_dir.iterdir() 
                      if f.is_file() and f.suffix in ['.wav', '.mp3', '.m4a']]
        if audio_files:
            return max(audio_files, key=lambda f: f.stat().st_mtime)
        
        return None
    
    def cleanup_temp_files(self):
        """
        Remove all temporary audio files to save storage space.
        """
        try:
            for file_path in self.output_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
                    print(f"Removed: {file_path.name}")
            print("Temporary audio files cleaned up")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


def test_download():
    """
    Test function to download audio from a sample Dinger City video.
    Replace the URL with an actual Dinger City video URL for testing.
    """
    # Dinger City video URL for testing
    test_url = "https://www.youtube.com/watch?v=5pbQOPeq_dU"
    
    downloader = AudioDownloader()
    
    print("Testing audio download...")
    audio_file = downloader.download_audio(test_url)
    
    if audio_file:
        print(f"Test successful! Audio saved to: {audio_file}")
        
        # Check file size to ensure it downloaded properly
        file_size = os.path.getsize(audio_file) / (1024 * 1024)  # Convert to MB
        print(f"File size: {file_size:.2f} MB")
        
        # Cleanup after test (comment out if you want to keep the file)
        # downloader.cleanup_temp_files()
    else:
        print("Test failed - could not download audio")


if __name__ == "__main__":
    # Run test when script is executed directly
    print("Mario Baseball Audio Downloader")
    print("================================")
    
    # Test with the provided Dinger City video
    test_download()
    
    print("\nTo use this module:")
    print("1. Replace the test_url in test_download() with a real Dinger City video URL")
    print("2. Uncomment the test_download() call")
    print("3. Run the script to test the download functionality")