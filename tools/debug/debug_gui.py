"""
DingerStats Debug GUI
Tkinter-based graphical interface for inspecting database contents and data quality
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.db_manager import DatabaseManager
from src.utils.player_normalizer import normalize_player_name
from src.utils.game_type_normalizer import normalize_game_type

class DingerStatsDebugGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DingerStats Debug Tool")
        self.root.geometry("1000x700")

        # Database connection
        self.db = DatabaseManager()

        # Create main layout
        self.create_widgets()

        # Load initial data
        self.refresh_all()

    def create_widgets(self):
        """Create the GUI layout"""

        # Top toolbar
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text="DingerStats Debug Tool", font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Button(toolbar, text="Refresh All", command=self.refresh_all).pack(side=tk.RIGHT, padx=5)

        # Main content area with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Overview
        self.overview_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_tab, text="Overview")
        self.create_overview_tab()

        # Tab 2: Video Coverage
        self.coverage_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.coverage_tab, text="Video Coverage")
        self.create_coverage_tab()

        # Tab 3: Game Types
        self.game_types_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.game_types_tab, text="Game Types")
        self.create_game_types_tab()

        # Tab 4: Player Stats
        self.player_stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.player_stats_tab, text="Player Stats")
        self.create_player_stats_tab()

        # Tab 5: Recent Games
        self.recent_games_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.recent_games_tab, text="Recent Games")
        self.create_recent_games_tab()

        # Tab 6: Processing Progress
        self.progress_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_tab, text="Progress & Quotas")
        self.create_progress_tab()

    def create_overview_tab(self):
        """Overview statistics"""
        frame = ttk.Frame(self.overview_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Stats labels
        self.overview_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=30, font=("Courier", 10))
        self.overview_text.pack(fill=tk.BOTH, expand=True)

    def create_coverage_tab(self):
        """Video coverage by playlist"""
        frame = ttk.Frame(self.coverage_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for coverage
        columns = ("Playlist", "Total", "Analyzed", "Percentage")
        self.coverage_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.coverage_tree.heading(col, text=col)
            self.coverage_tree.column(col, width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.coverage_tree.yview)
        self.coverage_tree.configure(yscrollcommand=scrollbar.set)

        self.coverage_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_game_types_tab(self):
        """Game type distribution"""
        frame = ttk.Frame(self.game_types_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Prompt version selector
        selector_frame = ttk.Frame(frame)
        selector_frame.pack(fill=tk.X, pady=5)

        ttk.Label(selector_frame, text="Prompt Version:").pack(side=tk.LEFT, padx=5)
        self.version_var = tk.StringVar(value="All")
        version_dropdown = ttk.Combobox(selector_frame, textvariable=self.version_var,
                                       values=["All", "v1", "v2"], state="readonly", width=15)
        version_dropdown.pack(side=tk.LEFT, padx=5)
        version_dropdown.bind("<<ComboboxSelected>>", lambda e: self.load_game_types())

        # Treeview for game types
        columns = ("Count", "Game Type", "Normalized")
        self.game_types_tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)

        self.game_types_tree.heading("Count", text="Count")
        self.game_types_tree.heading("Game Type", text="Raw Game Type")
        self.game_types_tree.heading("Normalized", text="Normalized")

        self.game_types_tree.column("Count", width=80)
        self.game_types_tree.column("Game Type", width=400)
        self.game_types_tree.column("Normalized", width=300)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.game_types_tree.yview)
        self.game_types_tree.configure(yscrollcommand=scrollbar.set)

        self.game_types_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_player_stats_tab(self):
        """Player statistics"""
        frame = ttk.Frame(self.player_stats_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for player stats
        columns = ("Player", "Games", "Wins", "Losses", "Win %")
        self.player_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.player_tree.heading(col, text=col)

        self.player_tree.column("Player", width=250)
        self.player_tree.column("Games", width=100)
        self.player_tree.column("Wins", width=100)
        self.player_tree.column("Losses", width=100)
        self.player_tree.column("Win %", width=100)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.player_tree.yview)
        self.player_tree.configure(yscrollcommand=scrollbar.set)

        self.player_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_recent_games_tab(self):
        """Recent games"""
        frame = ttk.Frame(self.recent_games_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Controls
        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X, pady=5)

        ttk.Label(controls, text="Show last:").pack(side=tk.LEFT, padx=5)
        self.limit_var = tk.StringVar(value="20")
        limit_spin = ttk.Spinbox(controls, from_=5, to=100, textvariable=self.limit_var, width=10)
        limit_spin.pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Load", command=self.load_recent_games).pack(side=tk.LEFT, padx=5)

        # Treeview for recent games
        columns = ("Player A", "Player B", "Score", "Winner", "Type", "Version")
        self.games_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        self.games_tree.heading("Player A", text="Player A")
        self.games_tree.heading("Player B", text="Player B")
        self.games_tree.heading("Score", text="Score")
        self.games_tree.heading("Winner", text="Winner")
        self.games_tree.heading("Type", text="Game Type")
        self.games_tree.heading("Version", text="Prompt")

        self.games_tree.column("Player A", width=150)
        self.games_tree.column("Player B", width=150)
        self.games_tree.column("Score", width=80)
        self.games_tree.column("Winner", width=150)
        self.games_tree.column("Type", width=250)
        self.games_tree.column("Version", width=80)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)

        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_progress_tab(self):
        """Processing progress and API quotas"""
        frame = ttk.Frame(self.progress_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # API Quota Info
        quota_frame = ttk.LabelFrame(frame, text="API Quotas", padding="10")
        quota_frame.pack(fill=tk.X, pady=5)

        self.quota_text = tk.Text(quota_frame, height=8, font=("Courier", 10), wrap=tk.WORD)
        self.quota_text.pack(fill=tk.X)

        # Playlist Progress
        progress_frame = ttk.LabelFrame(frame, text="Playlist Processing Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Canvas for progress bars
        canvas = tk.Canvas(progress_frame)
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=canvas.yview)
        self.progress_inner_frame = ttk.Frame(canvas)

        self.progress_inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrolleregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.progress_inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_all(self):
        """Refresh all data"""
        self.load_overview()
        self.load_coverage()
        self.load_game_types()
        self.load_player_stats()
        self.load_recent_games()
        self.load_progress_and_quotas()

    def load_overview(self):
        """Load overview statistics"""
        self.overview_text.delete(1.0, tk.END)

        with self.db.get_connection() as conn:
            # Total videos
            cursor = conn.execute("SELECT COUNT(*) FROM videos")
            total_videos = cursor.fetchone()[0]

            # Total games
            cursor = conn.execute("SELECT COUNT(*) FROM game_results")
            total_games = cursor.fetchone()[0]

            # By prompt version
            cursor = conn.execute("""
                SELECT prompt_version, COUNT(*)
                FROM game_results
                GROUP BY prompt_version
            """)
            versions = cursor.fetchall()

            # Players
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT player_a) + COUNT(DISTINCT player_b) FROM game_results
            """)
            unique_players = cursor.fetchone()[0]

        # Format output
        output = "="*60 + "\n"
        output += "  DINGERSTATS DATABASE OVERVIEW\n"
        output += "="*60 + "\n\n"
        output += f"Total Videos in Database: {total_videos}\n"
        output += f"Total Games Analyzed:     {total_games}\n"
        output += f"Unique Players:           {unique_players}\n\n"

        output += "Prompt Versions:\n"
        for version, count in versions:
            ver = version or 'unknown'
            output += f"  {ver:10} {count:4} games\n"

        output += "\n" + "="*60 + "\n"
        output += "Coverage Rate: {:.1f}%\n".format((total_games / total_videos * 100) if total_videos > 0 else 0)

        self.overview_text.insert(1.0, output)

    def load_coverage(self):
        """Load video coverage data"""
        # Clear existing data
        for item in self.coverage_tree.get_children():
            self.coverage_tree.delete(item)

        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    v.playlist_id,
                    COUNT(v.video_id) as total_videos,
                    COUNT(gr.video_id) as analyzed_videos
                FROM videos v
                LEFT JOIN game_results gr ON v.video_id = gr.video_id
                GROUP BY v.playlist_id
                ORDER BY analyzed_videos DESC
            """)

            for row in cursor.fetchall():
                playlist_id = row['playlist_id']
                total = row['total_videos']
                analyzed = row['analyzed_videos']
                pct = (analyzed / total * 100) if total > 0 else 0

                # Determine playlist name
                if 'x2Thksr' in playlist_id:
                    name = "Classic 10"
                elif 'lmNdN4W' in playlist_id:
                    name = "Season 10"
                else:
                    name = playlist_id[:15]

                self.coverage_tree.insert("", tk.END, values=(name, total, analyzed, f"{pct:.1f}%"))

    def load_game_types(self):
        """Load game type distribution"""
        # Clear existing data
        for item in self.game_types_tree.get_children():
            self.game_types_tree.delete(item)

        version_filter = self.version_var.get()

        with self.db.get_connection() as conn:
            if version_filter == "All":
                cursor = conn.execute("""
                    SELECT game_type, COUNT(*) as count
                    FROM game_results
                    GROUP BY game_type
                    ORDER BY count DESC
                """)
            else:
                cursor = conn.execute("""
                    SELECT game_type, COUNT(*) as count
                    FROM game_results
                    WHERE prompt_version = ?
                    GROUP BY game_type
                    ORDER BY count DESC
                """, (version_filter,))

            for row in cursor.fetchall():
                game_type = row['game_type'] or 'Unknown'
                count = row['count']
                normalized = normalize_game_type(game_type)

                self.game_types_tree.insert("", tk.END, values=(count, game_type, normalized))

    def load_player_stats(self):
        """Load player statistics"""
        # Clear existing data
        for item in self.player_tree.get_children():
            self.player_tree.delete(item)

        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    player_a as player,
                    COUNT(*) as games_played,
                    SUM(CASE WHEN winner = player_a THEN 1 ELSE 0 END) as wins
                FROM game_results
                WHERE player_a IS NOT NULL
                GROUP BY player_a
                UNION ALL
                SELECT
                    player_b as player,
                    COUNT(*) as games_played,
                    SUM(CASE WHEN winner = player_b THEN 1 ELSE 0 END) as wins
                FROM game_results
                WHERE player_b IS NOT NULL
                GROUP BY player_b
            """)

            # Aggregate by player
            player_stats = {}
            for row in cursor.fetchall():
                player = normalize_player_name(row['player'])
                if player not in player_stats:
                    player_stats[player] = {'games': 0, 'wins': 0}
                player_stats[player]['games'] += row['games_played']
                player_stats[player]['wins'] += row['wins']

            # Sort by games played
            sorted_players = sorted(player_stats.items(), key=lambda x: x[1]['games'], reverse=True)

            for player, stats in sorted_players:
                games = stats['games']
                wins = stats['wins']
                losses = games - wins
                win_pct = (wins / games * 100) if games > 0 else 0

                self.player_tree.insert("", tk.END, values=(
                    player, games, wins, losses, f"{win_pct:.1f}%"
                ))

    def load_recent_games(self):
        """Load recent games"""
        # Clear existing data
        for item in self.games_tree.get_children():
            self.games_tree.delete(item)

        try:
            limit = int(self.limit_var.get())
        except:
            limit = 20

        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    gr.player_a,
                    gr.player_b,
                    gr.score_a,
                    gr.score_b,
                    gr.winner,
                    gr.game_type,
                    gr.prompt_version
                FROM game_results gr
                ORDER BY gr.analyzed_at DESC
                LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                player_a = normalize_player_name(row['player_a']) or 'Unknown'
                player_b = normalize_player_name(row['player_b']) or 'Unknown'
                score = f"{row['score_a'] or '?'}-{row['score_b'] or '?'}"
                winner = normalize_player_name(row['winner']) or 'Unknown'
                game_type = normalize_game_type(row['game_type']) or 'Unknown'
                prompt_ver = row['prompt_version'] or 'v1'

                self.games_tree.insert("", tk.END, values=(
                    player_a, player_b, score, winner, game_type, prompt_ver
                ))

    def load_progress_and_quotas(self):
        """Load processing progress and API quotas"""
        # Clear quota text
        self.quota_text.delete(1.0, tk.END)

        # API Quota Information
        with self.db.get_connection() as conn:
            # Count total API requests made today
            cursor = conn.execute("""
                SELECT COUNT(*) FROM game_results
                WHERE DATE(analyzed_at) = DATE('now')
            """)
            today_requests = cursor.fetchone()[0]

            # Count total games
            cursor = conn.execute("SELECT COUNT(*) FROM game_results")
            total_games = cursor.fetchone()[0]

        # Gemini API: 1,500 requests/day free tier
        gemini_limit = 1500
        gemini_remaining = gemini_limit - today_requests

        quota_info = "="*60 + "\n"
        quota_info += "API QUOTA STATUS\n"
        quota_info += "="*60 + "\n\n"
        quota_info += f"Gemini API (Free Tier):\n"
        quota_info += f"  Daily Limit:     {gemini_limit:,} requests\n"
        quota_info += f"  Used Today:      {today_requests:,} requests\n"
        quota_info += f"  Remaining:       {gemini_remaining:,} requests\n"
        quota_info += f"  Usage:           {(today_requests/gemini_limit*100):.1f}%\n"
        quota_info += f"\nTotal Games Ever: {total_games:,}\n"

        self.quota_text.insert(1.0, quota_info)

        # Clear existing progress bars
        for widget in self.progress_inner_frame.winfo_children():
            widget.destroy()

        # Get playlist progress
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    v.playlist_id,
                    COUNT(v.video_id) as total_videos,
                    COUNT(gr.video_id) as analyzed_videos
                FROM videos v
                LEFT JOIN game_results gr ON v.video_id = gr.video_id
                GROUP BY v.playlist_id
                HAVING total_videos > 0
                ORDER BY analyzed_videos DESC
            """)
            playlists = cursor.fetchall()

        # Create progress bars for each playlist
        for i, playlist in enumerate(playlists):
            playlist_id = playlist['playlist_id']
            total = playlist['total_videos']
            analyzed = playlist['analyzed_videos']
            pct = (analyzed / total * 100) if total > 0 else 0

            # Determine playlist name
            if 'x2Thksr' in playlist_id:
                name = "Classic 10"
            elif 'lmNdN4W' in playlist_id:
                name = "Season 10"
            else:
                name = playlist_id[:20]

            # Create frame for this playlist
            playlist_frame = ttk.Frame(self.progress_inner_frame)
            playlist_frame.pack(fill=tk.X, padx=10, pady=5)

            # Label
            label_text = f"{name:20} {analyzed:3}/{total:3} videos ({pct:5.1f}%)"
            ttk.Label(playlist_frame, text=label_text, font=("Courier", 10)).pack(anchor=tk.W)

            # Progress bar
            progress = ttk.Progressbar(playlist_frame, length=700, mode='determinate', value=pct)
            progress.pack(fill=tk.X, pady=2)

            # Estimate remaining
            remaining = total - analyzed
            if remaining > 0:
                est_text = f"  → {remaining} videos remaining (~{remaining//10} minutes at 10/min)"
                ttk.Label(playlist_frame, text=est_text, font=("Courier", 9), foreground="gray").pack(anchor=tk.W)

def main():
    root = tk.Tk()
    app = DingerStatsDebugGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
