"""
Migration: Add game_type, game_summary, and commentary_summary columns
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('database/dingerstats.db')
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(game_results)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'game_type' not in columns:
            print("Adding game_type column...")
            cursor.execute("ALTER TABLE game_results ADD COLUMN game_type TEXT")

        if 'game_summary' not in columns:
            print("Adding game_summary column...")
            cursor.execute("ALTER TABLE game_results ADD COLUMN game_summary TEXT")

        if 'commentary_summary' not in columns:
            print("Adding commentary_summary column...")
            cursor.execute("ALTER TABLE game_results ADD COLUMN commentary_summary TEXT")

        conn.commit()
        print("Migration complete!")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
