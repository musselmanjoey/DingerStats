"""
CLI tool to mark videos as games or non-games
Useful for filtering out draft videos, analysis videos, etc.
"""

import sys
import os
import argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager

# Playlist IDs
PLAYLISTS = {
    'classic10': 'PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF',
    'season10': 'PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2',
}


def list_videos(playlist_key, show_all=False):
    """List videos in a playlist"""
    db = DatabaseManager()

    if playlist_key not in PLAYLISTS:
        print(f"ERROR: Unknown playlist '{playlist_key}'")
        print(f"Available playlists: {', '.join(PLAYLISTS.keys())}")
        return

    playlist_id = PLAYLISTS[playlist_key]
    videos = db.get_videos_by_playlist(playlist_id, include_non_games=show_all)

    print(f"\n{'='*80}")
    print(f"VIDEOS IN {playlist_key.upper()}")
    print(f"{'='*80}")
    print(f"Total: {len(videos)} video(s)")
    if not show_all:
        print("(Showing only games. Use --all to show non-games too)")
    print()

    for i, video in enumerate(videos, 1):
        is_game = video.get('is_game', 1)
        manual = video.get('manual_review', 0)
        status = "GAME" if is_game else "NOT A GAME"
        flag = " [MANUAL]" if manual else ""

        print(f"{i}. [{status}{flag}] {video['title'][:65]}")
        print(f"   ID: {video['video_id']}")
        print()


def mark_non_game(video_ids):
    """Mark videos as NOT games"""
    db = DatabaseManager()

    print(f"\nMarking {len(video_ids)} video(s) as NOT A GAME...")

    for video_id in video_ids:
        video = db.get_video(video_id)
        if not video:
            print(f"  ✗ {video_id}: Video not found in database")
            continue

        success = db.mark_video_as_non_game(video_id, manual=True)
        if success:
            print(f"  [OK] {video['title'][:60]}")
        else:
            print(f"  [FAIL] {video['title'][:60]}")

    print("\nDone!")


def mark_game(video_ids):
    """Mark videos as games (revert non-game status)"""
    db = DatabaseManager()

    print(f"\nMarking {len(video_ids)} video(s) as GAME...")

    for video_id in video_ids:
        video = db.get_video(video_id)
        if not video:
            print(f"  ✗ {video_id}: Video not found in database")
            continue

        success = db.mark_video_as_game(video_id, manual=True)
        if success:
            print(f"  [OK] {video['title'][:60]}")
        else:
            print(f"  [FAIL] {video['title'][:60]}")

    print("\nDone!")


def main():
    parser = argparse.ArgumentParser(
        description='Mark videos as games or non-games',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all videos in Classic 10 playlist
  python mark_videos.py --list classic10

  # List all videos including non-games
  python mark_videos.py --list classic10 --all

  # Mark a video as NOT a game (draft, analysis, etc.)
  python mark_videos.py --not-game DvVBLhsfaBs

  # Mark multiple videos as NOT games
  python mark_videos.py --not-game DvVBLhsfaBs abc123 xyz789

  # Mark a video as a game (revert non-game status)
  python mark_videos.py --game DvVBLhsfaBs
        """
    )

    parser.add_argument(
        '--list',
        choices=list(PLAYLISTS.keys()),
        help='List videos in a playlist'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all videos including non-games (use with --list)'
    )

    parser.add_argument(
        '--not-game',
        nargs='+',
        metavar='VIDEO_ID',
        help='Mark video(s) as NOT a game'
    )

    parser.add_argument(
        '--game',
        nargs='+',
        metavar='VIDEO_ID',
        help='Mark video(s) as a game'
    )

    args = parser.parse_args()

    # Run the appropriate command
    if args.list:
        list_videos(args.list, show_all=args.all)
    elif args.not_game:
        mark_non_game(args.not_game)
    elif args.game:
        mark_game(args.game)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
