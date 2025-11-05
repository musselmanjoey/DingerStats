"""
Processing statistics endpoint
"""
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

class ProcessingStats:
    def __init__(self, db_path="../../database/dingerstats.db"):
        self.db = DatabaseManager(db_path)
    
    def get_stats(self):
        """Get processing statistics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute('SELECT COUNT(*) FROM videos')
        total_videos = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM game_results')
        processed = cursor.fetchone()[0]
        
        remaining = total_videos - processed
        
        # Free tier: 50 videos/day
        free_tier_days = remaining / 50
        free_tier_completion = datetime.now() + timedelta(days=free_tier_days)
        
        # Paid tier estimate: ~500 videos/day (parallel processing)
        paid_tier_days = remaining / 500
        
        # Cost per video estimate: ~$0.003
        cost_per_video = 0.003
        total_cost = remaining * cost_per_video
        
        return {
            'total_videos': total_videos,
            'processed': processed,
            'remaining': remaining,
            'progress_pct': round((processed / total_videos) * 100, 1),
            'free_tier': {
                'days_remaining': round(free_tier_days, 1),
                'completion_date': free_tier_completion.strftime('%B %d, %Y'),
                'videos_per_day': 50
            },
            'paid_tier': {
                'days_to_complete': round(paid_tier_days, 1),
                'cost_estimate': round(total_cost, 2)
            }
        }
    
    def calculate_donation_impact(self, donation_amount):
        """Calculate how much a donation speeds up processing"""
        cost_per_video = 0.003
        videos_funded = int(donation_amount / cost_per_video)
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM videos')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM game_results')
        processed = cursor.fetchone()[0]
        remaining = total - processed
        
        # Days saved on free tier (50/day)
        days_saved = min(videos_funded / 50, remaining / 50)
        
        return {
            'videos_funded': videos_funded,
            'days_saved': round(days_saved, 1),
            'can_complete_all': videos_funded >= remaining,
            'remaining': remaining
        }

if __name__ == "__main__":
    stats = ProcessingStats()
    import json
    print(json.dumps(stats.get_stats(), indent=2))
    print("\n$5 donation impact:")
    print(json.dumps(stats.calculate_donation_impact(5), indent=2))
