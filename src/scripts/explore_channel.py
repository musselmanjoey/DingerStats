"""
Quick script to explore Dinger City channel and playlists
"""

import os
from dotenv import load_dotenv
from youtube_fetcher import YouTubeFetcher

# Load environment variables
load_dotenv()

def main():
    channel_url = "https://www.youtube.com/@DingerCity"

    print("="*60)
    print("EXPLORING DINGER CITY CHANNEL")
    print("="*60)
    print(f"Channel URL: {channel_url}\n")

    try:
        fetcher = YouTubeFetcher()

        # Get channel ID
        print("Getting channel ID...")
        channel_id = fetcher.get_channel_id_from_url(channel_url)

        if not channel_id:
            print("ERROR: Could not find channel ID")
            return

        print(f"[OK] Channel ID: {channel_id}\n")

        # Get all playlists
        print("Fetching all playlists...\n")
        playlists = fetcher.get_channel_playlists(channel_id)

        if not playlists:
            print("No playlists found")
            return

        print(f"Found {len(playlists)} playlists:")
        print("="*60)

        for i, playlist in enumerate(playlists, 1):
            print(f"\n{i}. {playlist['title']}")
            print(f"   Playlist ID: {playlist['playlist_id']}")
            print(f"   Videos: {playlist['video_count']}")
            if playlist['description']:
                desc = playlist['description'][:100]
                print(f"   Description: {desc}{'...' if len(playlist['description']) > 100 else ''}")

        print("\n" + "="*60)
        print("\nTo fetch videos from a playlist, use:")
        print("python process_dinger_videos.py fetch --playlist PLAYLIST_ID")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
