"""
DingerStats Main Pipeline
Fetch videos from Dinger City, analyze with Gemini, and store results
"""

import os
import sys
import time
import argparse
from typing import List, Dict
from dotenv import load_dotenv

from youtube_fetcher import YouTubeFetcher
from gemini_analyzer import GeminiAnalyzer
from database.db_manager import DatabaseManager


class DingerStatsPipeline:
    def __init__(self, youtube_api_key: str = None, gemini_api_key: str = None):
        """Initialize the pipeline with API clients and database"""
        # Load environment variables
        load_dotenv()

        # Initialize components
        self.youtube = YouTubeFetcher(youtube_api_key)
        self.gemini = GeminiAnalyzer(gemini_api_key)
        self.db = DatabaseManager()

        print("[OK] Pipeline initialized")
        print(f"  - Database: {self.db.db_path}")
        print(f"  - YouTube API: Ready")
        print(f"  - Gemini API: Ready")

    def fetch_and_store_playlist_videos(self, playlist_id: str,
                                         title_filters: List[str] = None,
                                         exclude_filters: List[str] = None,
                                         max_videos: int = None) -> List[Dict]:
        """
        Fetch videos from a playlist and store in database

        Args:
            playlist_id: YouTube playlist ID
            title_filters: List of regex patterns to include (e.g., ["Mario Baseball", "Super Sluggers"])
            exclude_filters: List of regex patterns to exclude (e.g., ["Trailer", "Announcement"])
            max_videos: Maximum number of videos to fetch

        Returns:
            List of video dictionaries
        """
        print(f"\nFetching videos from playlist: {playlist_id}")

        # Fetch all videos from playlist
        videos = self.youtube.get_playlist_videos(playlist_id, max_results=max_videos)
        print(f"  Found {len(videos)} videos")

        # Apply filters
        if title_filters or exclude_filters:
            videos = self.youtube.filter_videos_by_title(videos, title_filters or [], exclude_filters)
            print(f"  After filtering: {len(videos)} videos")

        # Store in database
        if videos:
            count = self.db.batch_insert_videos(videos)
            print(f"  Stored {count} videos in database")

        return videos

    def fetch_and_store_channel_videos(self, channel_id: str,
                                        search_query: str = "",
                                        max_videos: int = 50) -> List[Dict]:
        """
        Search and fetch videos from a channel

        Args:
            channel_id: YouTube channel ID
            search_query: Search query
            max_videos: Maximum results

        Returns:
            List of video dictionaries
        """
        print(f"\nSearching channel {channel_id} for: '{search_query}'")

        videos = self.youtube.search_channel_videos(channel_id, search_query, max_videos)
        print(f"  Found {len(videos)} videos")

        if videos:
            count = self.db.batch_insert_videos(videos)
            print(f"  Stored {count} videos in database")

        return videos

    def analyze_video(self, video_id: str, video_url: str = None) -> bool:
        """
        Analyze a single video and store result

        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL (optional)

        Returns:
            True if successful, False otherwise
        """
        # Mark as processing
        self.db.update_processing_status(video_id, 'processing')

        try:
            # Analyze with Gemini
            result, raw_response = self.gemini.analyze_game_video(video_id, video_url)

            if result:
                # Store result
                result['video_id'] = video_id
                result['raw_response'] = raw_response
                success = self.db.insert_game_result(result)

                if success:
                    self.db.update_processing_status(video_id, 'completed')
                    # Display player names (primary) and team names (secondary)
                    player_display = f"{result.get('player_a', '?')} vs {result.get('player_b', '?')}"
                    team_display = f"({result.get('team_a', '?')} vs {result.get('team_b', '?')})"
                    print(f"  [OK] {player_display} {team_display} - Winner: {result['winner']}")
                    return True
                else:
                    self.db.update_processing_status(video_id, 'failed', 'Failed to store result')
                    print(f"  [FAIL] Failed to store result")
                    return False
            else:
                self.db.update_processing_status(video_id, 'failed', 'Gemini analysis failed')
                print(f"  [FAIL] Gemini analysis failed")
                return False

        except Exception as e:
            error_msg = str(e)
            self.db.update_processing_status(video_id, 'failed', error_msg)
            print(f"  [FAIL] Error - {error_msg}")
            return False

    def process_unanalyzed_videos(self, max_videos: int = None, delay: float = 6.0):
        """
        Process all videos that haven't been analyzed yet

        Args:
            max_videos: Maximum number of videos to process (None = all)
            delay: Delay in seconds between API calls (default 6 for free tier rate limit)

        Note: Gemini API only supports 1 YouTube video per request
        Free tier: 250 requests/day, so max 250 videos/day
        """
        print("\nProcessing unanalyzed videos...")

        # Get unprocessed videos
        videos = self.db.get_unprocessed_videos()

        if not videos:
            print("  No unprocessed videos found")
            return

        print(f"  Found {len(videos)} unprocessed videos")

        # Limit if specified
        if max_videos:
            videos = videos[:max_videos]
            print(f"  Processing first {len(videos)} videos")

        print(f"  Rate limit: {delay}s between requests\n")

        success_count = 0
        for i, video in enumerate(videos, 1):
            print(f"[{i}/{len(videos)}] {video['title'][:70]}...")

            if self.analyze_video(video['video_id']):
                success_count += 1

            # Rate limiting
            if i < len(videos):  # Don't sleep after last video
                time.sleep(delay)

        print(f"\n{'='*60}")
        print(f"COMPLETE: {success_count}/{len(videos)} successful ({success_count/len(videos)*100:.1f}%)")
        print("="*60)

    def show_stats(self):
        """Display database statistics"""
        stats = self.db.get_stats()

        print("\n" + "="*60)
        print("DATABASE STATISTICS")
        print("="*60)
        print(f"Total Videos: {stats['total_videos']}")
        print(f"Analyzed Videos: {stats['analyzed_videos']}")
        print(f"Pending Analysis: {stats['total_videos'] - stats['analyzed_videos']}")

        if stats['by_status']:
            print("\nProcessing Status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")

    def show_recent_results(self, limit: int = 10):
        """Display recent game results"""
        results = self.db.get_all_game_results()[:limit]

        if not results:
            print("\nNo results found")
            return

        print(f"\n{'='*60}")
        print(f"RECENT GAME RESULTS (showing {len(results)})")
        print("="*60)

        for result in results:
            print(f"\nVideo: {result.get('title', 'Unknown')}")
            # Show player names (primary)
            if result.get('player_a') and result.get('player_b'):
                print(f"  Players: {result['player_a']} vs {result['player_b']}")
            # Show team names (secondary)
            if result.get('team_a') and result.get('team_b'):
                print(f"  Teams: {result['team_a']} vs {result['team_b']}")
            print(f"  Score: {result['score_a']}-{result['score_b']}")
            print(f"  Winner: {result['winner']}")
            print(f"  Confidence: {result['confidence']}")


def main():
    # Load environment variables first
    load_dotenv()

    parser = argparse.ArgumentParser(description="DingerStats Video Processing Pipeline")

    # Command selection
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch videos from YouTube')
    fetch_parser.add_argument('--playlist', type=str, help='Playlist ID')
    fetch_parser.add_argument('--channel', type=str, help='Channel ID')
    fetch_parser.add_argument('--search', type=str, help='Search query')
    fetch_parser.add_argument('--filter', nargs='+', help='Title filters (regex)')
    fetch_parser.add_argument('--exclude', nargs='+', help='Exclude filters (regex)')
    fetch_parser.add_argument('--max', type=int, help='Maximum videos to fetch')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze videos with Gemini')
    analyze_parser.add_argument('--max', type=int, help='Maximum videos to process')
    analyze_parser.add_argument('--delay', type=float, default=6.0,
                                help='Delay between API calls (seconds, default 6)')

    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')

    # Results command
    results_parser = subparsers.add_parser('results', help='Show recent results')
    results_parser.add_argument('--limit', type=int, default=10, help='Number of results to show')

    args = parser.parse_args()

    # Check for API keys
    youtube_key = os.environ.get('YOUTUBE_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("ERROR: API keys not set")
        print("\nRequired environment variables:")
        if not youtube_key:
            print("  - YOUTUBE_API_KEY")
        if not gemini_key:
            print("  - GEMINI_API_KEY")
        print("\nCreate a .env file with your keys (see .env.example)")
        sys.exit(1)

    try:
        # Initialize pipeline
        pipeline = DingerStatsPipeline(youtube_key, gemini_key)

        if args.command == 'fetch':
            if args.playlist:
                pipeline.fetch_and_store_playlist_videos(
                    args.playlist,
                    title_filters=args.filter,
                    exclude_filters=args.exclude,
                    max_videos=args.max
                )
            elif args.channel:
                pipeline.fetch_and_store_channel_videos(
                    args.channel,
                    search_query=args.search or "",
                    max_videos=args.max or 50
                )
            else:
                print("ERROR: Must specify --playlist or --channel")

        elif args.command == 'analyze':
            pipeline.process_unanalyzed_videos(
                max_videos=args.max,
                delay=args.delay
            )

        elif args.command == 'stats':
            pipeline.show_stats()

        elif args.command == 'results':
            pipeline.show_recent_results(limit=args.limit)

        else:
            parser.print_help()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
