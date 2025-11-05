"""
Migration: Add player_a and player_b columns to game_results table
"""

import sqlite3

def migrate():
    conn = sqlite3.connect('database/dingerstats.db')
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(game_results)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'player_a' not in columns:
            print("Adding player_a column...")
            cursor.execute("ALTER TABLE game_results ADD COLUMN player_a TEXT")

        if 'player_b' not in columns:
            print("Adding player_b column...")
            cursor.execute("ALTER TABLE game_results ADD COLUMN player_b TEXT")

        conn.commit()
        print("Migration complete!")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
