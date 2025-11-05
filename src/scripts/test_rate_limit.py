"""
Test script to find optimal rate limit for Gemini API
Tests different delays to see what gets rate limited
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import time
from datetime import datetime
from dotenv import load_dotenv
from database.db_manager import DatabaseManager
from src.analyzers.gemini_analyzer import GeminiAnalyzer

load_dotenv()

def test_rate_limit():
    """Test different rate limits"""

    db = DatabaseManager()
    gemini = GeminiAnalyzer()

    # Get a few videos to test with
    CLASSIC_10_PLAYLIST = 'PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF'
    videos = db.get_videos_by_playlist(CLASSIC_10_PLAYLIST)[:5]

    delays = [3, 4, 5]  # Test different delays in seconds

    for delay in delays:
        print("\n" + "="*60)
        print(f"TESTING DELAY: {delay}s between requests")
        print("="*60)

        start_time = time.time()
        rate_limited_count = 0

        for i, video in enumerate(videos, 1):
            video_id = video['video_id']
            title = video['title']

            print(f"\n[{i}/5] {title[:50]}...")
            request_start = time.time()

            try:
                result, raw = gemini.analyze_game_video(
                    video_id=video_id,
                    prompt_version='v2'
                )

                request_time = time.time() - request_start

                # Check if we got rate limited (request took > 10s usually means retry happened)
                if request_time > 10:
                    rate_limited_count += 1
                    print(f"  [RATE LIMITED] Request took {request_time:.1f}s")
                else:
                    print(f"  [OK] Request took {request_time:.1f}s")

                if result:
                    print(f"  Winner: {result.get('winner')}, Type: {result.get('game_type')}")

                # Wait before next request
                if i < len(videos):
                    print(f"  Waiting {delay}s...")
                    time.sleep(delay)

            except Exception as e:
                print(f"  [ERROR] {e}")

        total_time = time.time() - start_time
        avg_time = total_time / len(videos)

        print("\n" + "-"*60)
        print(f"RESULTS FOR {delay}s DELAY:")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Avg per video: {avg_time:.1f}s")
        print(f"  Rate limited: {rate_limited_count}/{len(videos)}")
        print(f"  Estimated for 46 videos: {(avg_time * 46 / 60):.1f} minutes")
        print("-"*60)

        # Wait a bit between test runs
        if delay != delays[-1]:
            print("\nWaiting 30s before next test run...")
            time.sleep(30)

if __name__ == '__main__':
    test_rate_limit()
