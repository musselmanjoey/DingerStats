"""
YouTube Data API Client for DingerStats
Fetches playlists and videos from Dinger City channel
"""

import os
import re
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import isodate  # For parsing ISO 8601 duration


class YouTubeFetcher:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube Data API client"""
        self.api_key = api_key or os.environ.get('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YouTube API key required. Set YOUTUBE_API_KEY environment variable.")

        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_channel_id_from_url(self, channel_url: str) -> Optional[str]:
        """Extract channel ID from channel URL or handle"""
        # Handle different URL formats
        if 'youtube.com/channel/' in channel_url:
            return channel_url.split('youtube.com/channel/')[-1].split('/')[0]
        elif 'youtube.com/@' in channel_url or 'youtube.com/c/' in channel_url:
            # Need to search for channel by handle
            handle = channel_url.split('/')[-1].replace('@', '')
            return self.get_channel_id_by_handle(handle)
        return None

    def get_channel_id_by_handle(self, handle: str) -> Optional[str]:
        """Get channel ID from channel handle/username"""
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1
            )
            response = request.execute()

            if response['items']:
                return response['items'][0]['snippet']['channelId']
        except HttpError as e:
            print(f"Error fetching channel ID: {e}")
        return None

    def get_channel_playlists(self, channel_id: str) -> List[Dict]:
        """Get all playlists from a channel"""
        playlists = []
        next_page_token = None

        try:
            while True:
                request = self.youtube.playlists().list(
                    part="snippet,contentDetails",
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response['items']:
                    playlists.append({
                        'playlist_id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'video_count': item['contentDetails']['itemCount'],
                        'published_at': item['snippet']['publishedAt']
                    })

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

        except HttpError as e:
            print(f"Error fetching playlists: {e}")

        return playlists

    def get_playlist_videos(self, playlist_id: str, max_results: int = None) -> List[Dict]:
        """Get all videos from a playlist with full metadata"""
        video_ids = []
        next_page_token = None

        try:
            # First, get video IDs from playlist
            while True:
                request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                video_ids.extend([item['contentDetails']['videoId'] for item in response['items']])

                next_page_token = response.get('nextPageToken')
                if not next_page_token or (max_results and len(video_ids) >= max_results):
                    break

            # Limit results if specified
            if max_results:
                video_ids = video_ids[:max_results]

            # Now get full video details in batches of 50
            videos = []
            for i in range(0, len(video_ids), 50):
                batch = video_ids[i:i+50]
                video_details = self.get_video_details(batch)
                videos.extend(video_details)

            # Add playlist_id to each video
            for video in videos:
                video['playlist_id'] = playlist_id

            return videos

        except HttpError as e:
            print(f"Error fetching playlist videos: {e}")
            return []

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information for multiple videos"""
        if not video_ids:
            return []

        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=','.join(video_ids)
            )
            response = request.execute()

            videos = []
            for item in response['items']:
                # Parse duration from ISO 8601 format (PT1H2M30S)
                duration = isodate.parse_duration(item['contentDetails']['duration'])
                duration_str = str(duration)

                videos.append({
                    'video_id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'published_at': item['snippet']['publishedAt'],
                    'channel_id': item['snippet']['channelId'],
                    'duration': duration_str,
                    'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0))
                })

            return videos

        except HttpError as e:
            print(f"Error fetching video details: {e}")
            return []

    def filter_videos_by_title(self, videos: List[Dict], patterns: List[str],
                                exclude_patterns: List[str] = None) -> List[Dict]:
        """
        Filter videos by title using regex patterns

        Args:
            videos: List of video dictionaries
            patterns: List of regex patterns to match (include if any matches)
            exclude_patterns: List of regex patterns to exclude (exclude if any matches)

        Returns:
            Filtered list of videos
        """
        filtered = []

        for video in videos:
            title = video['title'].lower()

            # Check if title matches any include pattern
            if patterns:
                if not any(re.search(pattern.lower(), title) for pattern in patterns):
                    continue

            # Check if title matches any exclude pattern
            if exclude_patterns:
                if any(re.search(pattern.lower(), title) for pattern in exclude_patterns):
                    continue

            filtered.append(video)

        return filtered

    def search_channel_videos(self, channel_id: str, query: str = "",
                               max_results: int = 50) -> List[Dict]:
        """
        Search videos in a channel

        Args:
            channel_id: YouTube channel ID
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of video dictionaries
        """
        video_ids = []

        try:
            request = self.youtube.search().list(
                part="id",
                channelId=channel_id,
                q=query,
                type="video",
                maxResults=min(max_results, 50),
                order="date"
            )
            response = request.execute()

            video_ids = [item['id']['videoId'] for item in response['items']]

            # Get full details
            videos = self.get_video_details(video_ids)
            return videos

        except HttpError as e:
            print(f"Error searching videos: {e}")
            return []


def main():
    """Test the YouTube fetcher"""
    print("YouTube Data API Fetcher - Test Mode\n")

    # Check for API key
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("ERROR: YOUTUBE_API_KEY environment variable not set")
        print("\nTo set it:")
        print("  Windows: set YOUTUBE_API_KEY=your_key_here")
        print("  Linux/Mac: export YOUTUBE_API_KEY=your_key_here")
        return

    try:
        fetcher = YouTubeFetcher(api_key)

        # Example: Get channel info (replace with actual Dinger City channel)
        print("Enter Dinger City channel URL or ID:")
        print("Example: https://www.youtube.com/@DingerCity")
        channel_input = input("> ").strip()

        if channel_input:
            # Extract channel ID
            if channel_input.startswith('http'):
                channel_id = fetcher.get_channel_id_from_url(channel_input)
            else:
                channel_id = channel_input

            if not channel_id:
                print("Could not determine channel ID")
                return

            print(f"\nChannel ID: {channel_id}")

            # Get playlists
            print("\nFetching playlists...")
            playlists = fetcher.get_channel_playlists(channel_id)

            print(f"\nFound {len(playlists)} playlists:")
            for i, playlist in enumerate(playlists, 1):
                print(f"  {i}. {playlist['title']} ({playlist['video_count']} videos)")

            # Let user select a playlist
            if playlists:
                print("\nEnter playlist number to fetch videos (or press Enter to skip):")
                choice = input("> ").strip()

                if choice.isdigit() and 1 <= int(choice) <= len(playlists):
                    selected = playlists[int(choice) - 1]
                    print(f"\nFetching videos from: {selected['title']}")

                    videos = fetcher.get_playlist_videos(selected['playlist_id'], max_results=10)
                    print(f"\nFound {len(videos)} videos (showing first 10):")

                    for i, video in enumerate(videos, 1):
                        print(f"  {i}. {video['title']}")
                        print(f"     ID: {video['video_id']}, Duration: {video['duration']}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
