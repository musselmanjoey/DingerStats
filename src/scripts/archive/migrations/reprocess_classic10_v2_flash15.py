"""
Re-process remaining Classic 10 videos with v2 prompt using gemini-1.5-flash
This model has higher free tier limits (1,500/day vs 50/day for 2.0-flash-exp)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import time
from dotenv import load_dotenv
from database.db_manager import DatabaseManager
from src.analyzers.gemini_analyzer import GeminiAnalyzer
from src.config import PLAYLISTS

load_dotenv()

def reprocess_classic10_with_v2_flash15():
    """Re-process Classic 10 videos with v2 prompt using gemini-1.5-flash"""

    print("="*60)
    print("Re-processing Classic 10 with v2 Prompt (gemini-1.5-flash)")
    print("="*60)

    # Initialize with gemini-1.5-flash model
    db = DatabaseManager()
    gemini = GeminiAnalyzer(model='models/gemini-1.5-flash')

    # Classic 10 playlist ID
    CLASSIC_10_PLAYLIST = PLAYLISTS['classic10']

    # Get all Classic 10 videos
    all_videos = db.get_videos_by_playlist(CLASSIC_10_PLAYLIST)

    # Get videos that already have v2 results to skip them
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT video_id
            FROM game_results
            WHERE prompt_version = 'v2'
        """)
        processed_video_ids = {row['video_id'] for row in cursor.fetchall()}

    # Filter to only unprocessed videos
    videos = [v for v in all_videos if v['video_id'] not in processed_video_ids]

    print(f"\nTotal Classic 10 videos: {len(all_videos)}")
    print(f"Already processed with v2: {len(processed_video_ids)}")
    print(f"Remaining to process: {len(videos)}")
    print(f"Model: gemini-1.5-flash (1,500 requests/day limit)")
    print(f"Starting re-analysis with v2 prompt...\n")

    # Track stats
    success_count = 0
    failed_count = 0

    # Process each video
    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']

        print(f"\n[{i}/{len(videos)}] {title[:60]}...")

        try:
            # Analyze with v2 prompt using gemini-1.5-flash
            result, raw = gemini.analyze_game_video(
                video_id=video_id,
                prompt_version='v2'
            )

            if result:
                print(f"  Players: {result.get('player_a')} vs {result.get('player_b')}")
                print(f"  Winner: {result.get('winner')}")
                print(f"  Game Type: {result.get('game_type')}")
                print(f"  Prompt Version: {result.get('prompt_version')}")
                print(f"  Model: {result.get('model_name')}")

                # Store the v2 result
                result['video_id'] = video_id
                result['raw_response'] = raw
                db.insert_game_result(result)

                success_count += 1
                print(f"  [OK] Stored v2 result")
            else:
                print(f"  [FAILED] Could not parse result")
                failed_count += 1

            # Rate limiting: wait 4.5 seconds between requests
            # (gemini-1.5-flash: 15 requests/minute = 4s minimum)
            if i < len(videos):
                print(f"  Waiting 4.5s for rate limit...")
                time.sleep(4.5)

        except Exception as e:
            print(f"  [ERROR] {e}")
            failed_count += 1

            # Wait longer on error
            if i < len(videos):
                print(f"  Waiting 10s after error...")
                time.sleep(10)

    # Summary
    print("\n" + "="*60)
    print("Re-processing Complete!")
    print("="*60)
    print(f"Success: {success_count}/{len(videos)}")
    print(f"Failed:  {failed_count}/{len(videos)}")
    print(f"\nTotal v2 results: {len(processed_video_ids) + success_count}/{len(all_videos)}")
    print("\nYou can now compare v1 vs v2 data quality!")
    print("Note: Results tagged with model='gemini-1.5-flash'")

if __name__ == '__main__':
    reprocess_classic10_with_v2_flash15()
