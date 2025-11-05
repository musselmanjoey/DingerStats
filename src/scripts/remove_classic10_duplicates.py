"""
Remove duplicate game_results entries for Classic 10

When videos were reprocessed, duplicate entries were created.
This script keeps the entry with the most detailed game_type and removes others.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from database.db_manager import DatabaseManager

def remove_duplicates():
    """Remove duplicate game_results entries, keeping the best one"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    db_path = os.path.join(project_root, 'database', 'dingerstats.db')

    db = DatabaseManager(db_path)

    print("=" * 80)
    print("REMOVING DUPLICATE CLASSIC 10 GAME ENTRIES")
    print("=" * 80)

    with db.get_connection() as conn:
        # Find all duplicate video_ids
        cursor = conn.execute("""
            SELECT video_id, COUNT(*) as occurrences
            FROM game_results
            WHERE game_type LIKE '%Classic 10%'
            GROUP BY video_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()

        print(f"\nFound {len(duplicates)} videos with duplicate entries\n")

        total_removed = 0

        for dup in duplicates:
            video_id = dup['video_id']

            # Get all entries for this video_id
            cursor = conn.execute("""
                SELECT rowid, game_type, player_a, player_b, analyzed_at
                FROM game_results
                WHERE video_id = ?
                ORDER BY
                    CASE
                        WHEN game_type LIKE '%Round%' THEN 1
                        WHEN game_type LIKE '%Elimination%' THEN 2
                        WHEN game_type LIKE '%Finals%' THEN 3
                        ELSE 4
                    END,
                    analyzed_at DESC
            """, (video_id,))
            entries = cursor.fetchall()

            # Keep the first one (most specific/recent)
            keep_rowid = entries[0][0]  # rowid is first column
            keep_type = entries[0][1]   # game_type is second column

            print(f"Video {video_id}:")
            print(f"  Keeping: {keep_type}")

            # Delete the others
            for entry in entries[1:]:
                print(f"  Removing: {entry[1]}")  # game_type is second column
                conn.execute("DELETE FROM game_results WHERE rowid = ?", (entry[0],))  # rowid is first column
                total_removed += 1

        conn.commit()

        print(f"\n[SUCCESS] Removed {total_removed} duplicate entries")

        # Verify
        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM game_results
            WHERE game_type LIKE '%Classic 10%'
        """)
        total = cursor.fetchone()['count']

        cursor = conn.execute("""
            SELECT COUNT(DISTINCT video_id) as count
            FROM game_results
            WHERE game_type LIKE '%Classic 10%'
        """)
        unique = cursor.fetchone()['count']

        print(f"\nAfter cleanup:")
        print(f"  Total entries: {total}")
        print(f"  Unique videos: {unique}")
        print(f"  Duplicates remaining: {total - unique}")

if __name__ == '__main__':
    remove_duplicates()
    print("\nNext step: Run 'python webapp/generate_tournament_pages.py' to update the site")
