"""
Fetch all Classic and Season playlists from Dinger City
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from dotenv import load_dotenv
from src.analyzers.youtube_fetcher import YouTubeFetcher
from database.db_manager import DatabaseManager
from src.config import PLAYLISTS

# Load environment variables
load_dotenv()

def main():
    print("="*60)
    print("FETCHING CLASSICS AND SEASONS FROM DINGER CITY")
    print("="*60)

    # Initialize
    fetcher = YouTubeFetcher()
    db = DatabaseManager()

    # Define all Classic playlists
    classics = [
        ("Classic 10: YERR OUT!", PLAYLISTS['classic10']),
        ("Classic 9: TEAM or NO TEAM", "PL4KAbBInKJ-zzSUI8ADCmI10Yl5RMeIml"),
        ("Classic 8 - Moneyball", "PL4KAbBInKJ-watpCq-XwwBTjgn5AjT58k"),
        ("Classic 7 - Blind Auction", "PL4KAbBInKJ-yyT-gLQ64j7VG6KSVxLdP8"),
        ("Classic 6 XL: Mixed Stars", "PL4KAbBInKJ-xGvMQdGOcdyEaNHkw_5Qtn"),
        ("Classic 5: Stars ON, bets OFF", "PL4KAbBInKJ-zf_GX7SCJBs47yicPZSpJj"),
        ("Classic 4 XS: Big Balla, Extra Smalla", "PL4KAbBInKJ-x-om-vZAyf69jNYADtaWGW"),
        ("Classic 3 XL", "PL4KAbBInKJ-zMmxajj0WDcsuyy-zQZhhk"),
        ("Dinger City Classic 2: Auction Action!", "PL4KAbBInKJ-wBLz6tdZydtC1G5ApjDMWP"),
        ("Dinger City Classic Winter 2022", "PL4KAbBInKJ-yDgWyqkUlH4Yyk1n6STYka"),
    ]

    # Define all Season playlists
    seasons = [
        ("SEASON 10 (Spring 2024)", PLAYLISTS['season10']),
        ("SEASON 9! Summer 2022", "PL4KAbBInKJ-xA2ncS-VZ2nD8FwdHHEcHe"),
        ("SEASON 8! Fall 2021", "PL4KAbBInKJ-wQw1VMopYJckrA2SoAc-Ad"),
        ("Season 7", "PL4KAbBInKJ-zvXG_lrydLaKMJwpEKYZBG"),
        ("Season 6! Fall 2020", "PL4KAbBInKJ-z2a4JwDXq7TbGVnnMpF26q"),
        ("SEASON 5", "PL4KAbBInKJ-yP4FCc0c-_KUA8xbFx_iNb"),
        ("SEASON 4", "PL4KAbBInKJ-w7m8IIDB6kTR_XBxbtK6bV"),
        ("Season 3 Games", "PL4KAbBInKJ-ympPybmia38u94Fc8rDaYn"),
        ("Season 2 Games", "PL4KAbBInKJ-wL3Av4AbrRo_Q3FPKMmnc0"),
        ("Season 1 Games (Humble Beginnings)", "PL4KAbBInKJ-ym6-jBj4QMd3xV8ueuVWA-"),
    ]

    all_playlists = classics + seasons

    print(f"\nFetching {len(classics)} Classics and {len(seasons)} Seasons")
    print(f"Total: {len(all_playlists)} playlists\n")

    total_videos = 0
    total_stored = 0

    for i, (name, playlist_id) in enumerate(all_playlists, 1):
        print(f"\n[{i}/{len(all_playlists)}] {name}")
        print(f"Playlist ID: {playlist_id}")

        try:
            # Fetch videos
            videos = fetcher.get_playlist_videos(playlist_id)
            print(f"  Found {len(videos)} videos")

            if videos:
                # Store in database
                stored = db.batch_insert_videos(videos)
                print(f"  Stored {stored} videos in database")

                total_videos += len(videos)
                total_stored += stored

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total videos found: {total_videos}")
    print(f"Total videos stored: {total_stored}")

    # Show database stats
    print("\n")
    stats = db.get_stats()
    print(f"Database now contains:")
    print(f"  Total videos: {stats['total_videos']}")
    print(f"  Analyzed: {stats['analyzed_videos']}")
    print(f"  Pending: {stats['total_videos'] - stats['analyzed_videos']}")

    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("Videos are now in the database!")
    print("\nTo analyze them with Gemini:")
    print("  python process_dinger_videos.py analyze --max 10")
    print("\nNote: Free tier = 250 videos/day")
    print(f"With {stats['total_videos']} videos, you'll need ~{stats['total_videos']//250 + 1} days")
    print("Or upgrade to paid tier for faster processing")

if __name__ == "__main__":
    main()
