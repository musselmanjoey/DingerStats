"""
Generic video processing script for DingerStats
Works with any analyzer (Gemini, Ollama) and prompt version
"""

import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager
from src.analyzers.ollama_transcript_analyzer import OllamaTranscriptAnalyzer

# Playlist IDs
PLAYLISTS = {
    'classic10': 'PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF',
    'season10': 'PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2',
}


def get_analyzer(analyzer_type, prompt_version):
    """Get the appropriate analyzer instance"""
    if analyzer_type == 'ollama':
        return OllamaTranscriptAnalyzer(model="llama3.2:1b"), 'ollama_transcript'
    elif analyzer_type == 'gemini':
        # Import here to avoid dependency if not using Gemini
        from src.analyzers.gemini_analyzer import GeminiAnalyzer
        return GeminiAnalyzer(prompt_version=prompt_version), 'gemini_visual'
    else:
        raise ValueError(f"Unknown analyzer type: {analyzer_type}")


def process_videos(playlist_key, analyzer_type, prompt_version, max_videos=None):
    """
    Process videos from a playlist with specified analyzer

    Args:
        playlist_key: Key from PLAYLISTS dict (e.g., 'classic10', 'season10')
        analyzer_type: 'ollama' or 'gemini'
        prompt_version: 'v1', 'v2', etc.
        max_videos: Maximum number of videos to process (None = all)
    """
    # Initialize
    db = DatabaseManager()
    analyzer, db_analyzer_type = get_analyzer(analyzer_type, prompt_version)

    # Get playlist ID
    if playlist_key not in PLAYLISTS:
        print(f"ERROR: Unknown playlist '{playlist_key}'")
        print(f"Available playlists: {', '.join(PLAYLISTS.keys())}")
        return

    playlist_id = PLAYLISTS[playlist_key]

    # Get videos from playlist (exclude non-games)
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT video_id, title, published_at
            FROM videos
            WHERE playlist_id = ? AND is_game = 1
            ORDER BY published_at
        """, (playlist_id,))
        videos = cursor.fetchall()

    # Limit if specified
    if max_videos:
        videos = videos[:max_videos]

    print("=" * 80)
    print(f"VIDEO PROCESSING - {playlist_key.upper()}")
    print("=" * 80)
    print(f"Analyzer: {analyzer_type} (stored as: {db_analyzer_type})")
    print(f"Prompt Version: {prompt_version}")
    print(f"Total videos to process: {len(videos)}")
    print()

    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']

        print(f"[{i}/{len(videos)}] {title[:60]}")
        print(f"  Video ID: {video_id}")

        # Analyze
        result, raw_response = analyzer.analyze_game_video(video_id)

        if result:
            print(f"  SUCCESS:")
            print(f"    Players: {result.get('player_a')} vs {result.get('player_b')}")
            print(f"    Winner: {result.get('winner')}")
            print(f"    Score: {result.get('score_a')}-{result.get('score_b')}")
            print(f"    Game Type: {result.get('game_type')}")
            print(f"    Confidence: {result.get('confidence')}")

            # Store in database with metadata
            with db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO game_results
                    (video_id, player_a, player_b, team_a, team_b,
                     score_a, score_b, winner, game_type,
                     raw_response, analyzer_type, prompt_version, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_id,
                    result.get('player_a'),
                    result.get('player_b'),
                    result.get('team_a', result.get('player_a')),  # Default to player name
                    result.get('team_b', result.get('player_b')),
                    result.get('score_a'),
                    result.get('score_b'),
                    result.get('winner'),
                    result.get('game_type'),
                    raw_response,
                    db_analyzer_type,
                    prompt_version,
                    result.get('confidence', 'medium')
                ))
                conn.commit()

            success_count += 1
        else:
            print(f"  FAILED: {raw_response}")
            fail_count += 1

        print()

    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total: {len(videos)}")


def main():
    parser = argparse.ArgumentParser(
        description='Process Mario Baseball videos with any analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process Classic 10 with Ollama v2
  python process_videos.py --playlist classic10 --analyzer ollama --version v2

  # Process Season 10 with Gemini v2 (first 5 videos only)
  python process_videos.py --playlist season10 --analyzer gemini --version v2 --max 5

  # Process Classic 10 with Ollama v1
  python process_videos.py --playlist classic10 --analyzer ollama --version v1
        """
    )

    parser.add_argument(
        '--playlist',
        required=True,
        choices=list(PLAYLISTS.keys()),
        help='Playlist to process'
    )

    parser.add_argument(
        '--analyzer',
        required=True,
        choices=['ollama', 'gemini'],
        help='Analyzer type to use'
    )

    parser.add_argument(
        '--version',
        required=True,
        help='Prompt version (e.g., v1, v2, v3)'
    )

    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help='Maximum number of videos to process (default: all)'
    )

    args = parser.parse_args()

    process_videos(
        playlist_key=args.playlist,
        analyzer_type=args.analyzer,
        prompt_version=args.version,
        max_videos=args.max
    )


if __name__ == '__main__':
    main()
