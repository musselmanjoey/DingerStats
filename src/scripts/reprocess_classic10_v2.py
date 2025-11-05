"""
Re-process Classic 10 videos with v2 prompt for comparison with v1 data

This script will:
1. Get all Classic 10 videos from the database
2. Re-analyze them using the v2 prompt
3. Store results with prompt_version='v2'
4. Allow comparison of v1 vs v2 data quality
"""

import os
import time
from dotenv import load_dotenv
from database.db_manager import DatabaseManager
from gemini_analyzer import GeminiAnalyzer

# Load environment variables
load_dotenv()

def reprocess_classic10_with_v2():
    """Re-process Classic 10 videos with v2 prompt"""

    print("="*60)
    print("Re-processing Classic 10 with v2 Prompt")
    print("="*60)

    # Initialize
    db = DatabaseManager()
    gemini = GeminiAnalyzer()

    # Classic 10 playlist ID
    CLASSIC_10_PLAYLIST = 'PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF'

    # Get all Classic 10 videos
    videos = db.get_videos_by_playlist(CLASSIC_10_PLAYLIST)

    print(f"\nFound {len(videos)} Classic 10 videos")
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
            # Analyze with v2 prompt
            result, raw = gemini.analyze_game_video(
                video_id=video_id,
                prompt_version='v2'
            )

            if result:
                print(f"  Players: {result.get('player_a')} vs {result.get('player_b')}")
                print(f"  Winner: {result.get('winner')}")
                print(f"  Game Type: {result.get('game_type')}")
                print(f"  Prompt Version: {result.get('prompt_version')}")

                # Store the v2 result
                result['video_id'] = video_id
                result['raw_response'] = raw
                db.insert_game_result(result)

                success_count += 1
                print(f"  [OK] Stored v2 result")
            else:
                print(f"  [FAILED] Could not parse result")
                failed_count += 1

            # Rate limiting: wait 6 seconds between requests (10 per minute)
            if i < len(videos):
                print(f"  Waiting 6s for rate limit...")
                time.sleep(6)

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
    print("\nYou can now compare v1 vs v2 data quality!")
    print("Query: SELECT game_type, prompt_version, COUNT(*) FROM game_results GROUP BY game_type, prompt_version")

if __name__ == '__main__':
    reprocess_classic10_with_v2()
