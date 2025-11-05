"""
Compare v1 vs v2 prompt results for Classic 10

This script analyzes differences between v1 and v2 data to evaluate
which prompt produces better game type detection.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import sqlite3
from collections import Counter
from database.db_manager import DatabaseManager

def compare_versions():
    """Compare v1 and v2 prompt results"""

    print("="*70)
    print("Prompt Version Comparison: v1 vs v2")
    print("="*70)

    db = DatabaseManager()

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Get v1 results
        cursor.execute("""
            SELECT game_type, COUNT(*) as count
            FROM game_results
            WHERE prompt_version = 'v1'
            GROUP BY game_type
            ORDER BY count DESC
        """)
        v1_results = cursor.fetchall()

        # Get v2 results
        cursor.execute("""
            SELECT game_type, COUNT(*) as count
            FROM game_results
            WHERE prompt_version = 'v2'
            GROUP BY game_type
            ORDER BY count DESC
        """)
        v2_results = cursor.fetchall()

        # Get total counts
        cursor.execute("SELECT COUNT(*) FROM game_results WHERE prompt_version = 'v1'")
        v1_total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM game_results WHERE prompt_version = 'v2'")
        v2_total = cursor.fetchone()[0]

    # Display v1 results
    print("\nV1 PROMPT RESULTS")
    print("-"*70)
    print(f"Total games: {v1_total}")
    print("\nGame Type Distribution:")
    for game_type, count in v1_results:
        game_type_str = game_type or 'None'
        print(f"  {game_type_str:50} {count:3} ({count/v1_total*100:.1f}%)")

    # Display v2 results
    print("\n\nV2 PROMPT RESULTS")
    print("-"*70)
    print(f"Total games: {v2_total}")
    print("\nGame Type Distribution:")
    for game_type, count in v2_results:
        game_type_str = game_type or 'None'
        print(f"  {game_type_str:50} {count:3} ({count/v2_total*100:.1f}%)")

    # Analysis
    print("\n\nANALYSIS")
    print("-"*70)

    # Expected Classic 10 structure:
    # - Each round has multiple round-robin games + 1 elimination game
    # - 3 rounds + Finals
    # - Round 1: 6 players = 15 round-robin games + 1 elimination (16 total)
    # - Round 2: 5 players = 10 round-robin games + 1 elimination (11 total)
    # - Round 3: 4 players = 6 round-robin games + 1 elimination (7 total)
    # - Finals: 2 players = best of series

    print("\nExpected Classic 10 Structure (YERR OUT! format):")
    print("  Round 1: ~15 round-robin games + 1 elimination")
    print("  Round 2: ~10 round-robin games + 1 elimination")
    print("  Round 3: ~6 round-robin games + 1 elimination")
    print("  Finals: Championship games")
    print("  TOTAL elimination games should be: ~3-4 (one per round + finals)")

    # Count eliminations in each version
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # V1 elimination count
        cursor.execute("""
            SELECT COUNT(*)
            FROM game_results
            WHERE prompt_version = 'v1'
            AND (
                game_type LIKE '%elimination%'
                OR game_type LIKE '%Elimination%'
            )
        """)
        v1_elim_count = cursor.fetchone()[0]

        # V2 elimination count
        cursor.execute("""
            SELECT COUNT(*)
            FROM game_results
            WHERE prompt_version = 'v2'
            AND (
                game_type LIKE '%elimination%'
                OR game_type LIKE '%Elimination%'
            )
        """)
        v2_elim_count = cursor.fetchone()[0]

    print(f"\nElimination Game Counts:")
    print(f"  v1: {v1_elim_count} elimination games (expected: ~3-4)")
    print(f"  v2: {v2_elim_count} elimination games (expected: ~3-4)")

    if v2_elim_count < v1_elim_count and v2_elim_count >= 3:
        print("\n  [OK] v2 appears to have better elimination detection!")
        print("       Closer to expected structure.")
    elif v1_elim_count == v2_elim_count:
        print("\n  [=] Both versions detected the same number of elimination games")
    else:
        print(f"\n  [?] v2 detected {v2_elim_count} elimination games vs v1's {v1_elim_count}")

    print("\n" + "="*70)

if __name__ == '__main__':
    compare_versions()
