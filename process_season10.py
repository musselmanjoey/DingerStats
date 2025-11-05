"""
Process Season 10 videos with progress tracking
Run this overnight to analyze all Season 10 games
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

from youtube_fetcher import YouTubeFetcher
from gemini_analyzer import GeminiAnalyzer
from database.db_manager import DatabaseManager

# Load environment variables
load_dotenv()

# Season 10 playlist ID
SEASON_10_PLAYLIST = "PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

    # Also write to log file
    with open("season10_progress.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def save_progress(processed, total, successful, failed):
    """Save progress to a file for tracking"""
    with open("season10_progress.txt", "w") as f:
        f.write(f"Season 10 Processing Progress\n")
        f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"Processed: {processed}/{total} ({processed/total*100:.1f}%)\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Success rate: {successful/processed*100:.1f}% (if > 0)\n" if processed > 0 else "Success rate: N/A\n")

def main():
    log("="*60)
    log("SEASON 10 PROCESSING - STARTING")
    log("="*60)

    # Initialize
    try:
        db = DatabaseManager()
        gemini = GeminiAnalyzer()
        log("Pipeline initialized successfully")
    except Exception as e:
        log(f"ERROR: Failed to initialize: {e}")
        return

    # Get Season 10 videos from database
    log(f"Fetching Season 10 videos (Playlist: {SEASON_10_PLAYLIST})")
    season10_videos = db.get_videos_by_playlist(SEASON_10_PLAYLIST)

    if not season10_videos:
        log("ERROR: No Season 10 videos found in database")
        log("Run fetch_classics_and_seasons.py first!")
        return

    log(f"Found {len(season10_videos)} Season 10 videos")

    # Filter out already processed
    unprocessed = []
    for video in season10_videos:
        result = db.get_game_result(video['video_id'])
        if not result:
            unprocessed.append(video)

    if not unprocessed:
        log("All Season 10 videos already processed!")
        return

    log(f"{len(unprocessed)} videos need processing")
    log(f"Estimated time: ~{len(unprocessed) * 6 / 60:.1f} minutes at 6 sec/video")
    log("")

    # Process each video
    total = len(unprocessed)
    successful = 0
    failed = 0

    for i, video in enumerate(unprocessed, 1):
        log(f"[{i}/{total}] Processing: {video['title'][:60]}...")

        # Mark as processing
        db.update_processing_status(video['video_id'], 'processing')

        try:
            # Analyze with Gemini
            result, raw_response = gemini.analyze_game_video(video['video_id'])

            if result and result.get('player_a') and result.get('player_b'):
                # Store result
                result['video_id'] = video['video_id']
                result['raw_response'] = raw_response

                if db.insert_game_result(result):
                    db.update_processing_status(video['video_id'], 'completed')
                    successful += 1

                    # Log success
                    player_display = f"{result.get('player_a', '?')} vs {result.get('player_b', '?')}"
                    game_type = result.get('game_type', 'Unknown')
                    log(f"  SUCCESS: {player_display} - Winner: {result['winner']} [{game_type}]")
                else:
                    db.update_processing_status(video['video_id'], 'failed', 'Failed to store')
                    failed += 1
                    log(f"  FAILED: Could not store result")
            else:
                db.update_processing_status(video['video_id'], 'failed', 'Analysis failed')
                failed += 1
                log(f"  FAILED: Gemini could not extract data")

        except Exception as e:
            error_msg = str(e)
            db.update_processing_status(video['video_id'], 'failed', error_msg)
            failed += 1
            log(f"  ERROR: {error_msg}")

        # Save progress after each video
        save_progress(i, total, successful, failed)

        # Rate limiting (except after last video)
        if i < total:
            time.sleep(6)

    # Final summary
    log("")
    log("="*60)
    log("SEASON 10 PROCESSING - COMPLETE")
    log("="*60)
    log(f"Total processed: {total}")
    log(f"Successful: {successful}")
    log(f"Failed: {failed}")
    log(f"Success rate: {successful/total*100:.1f}%")
    log("")

    # Save final progress
    save_progress(total, total, successful, failed)

if __name__ == "__main__":
    main()
