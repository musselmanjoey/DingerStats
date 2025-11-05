"""
Gemini API Video Analyzer for DingerStats
Uses Gemini's native YouTube video understanding to extract game results
"""

import os
import re
import time
import backoff
from typing import Dict, Optional, Tuple, List
from google import genai
from google.genai import types
from google.api_core import exceptions


class GeminiAnalyzer:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini API client

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model to use (gemini-2.0-flash-exp, gemini-2.0-flash-thinking-exp, etc.)
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable.")

        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def analyze_video_with_retry(self, video_url: str, prompt: str, max_retries: int = 3) -> str:
        """
        Analyze video with retry logic that respects Gemini's rate limit delays

        Args:
            video_url: Full YouTube video URL
            prompt: Question/instruction for Gemini
            max_retries: Maximum number of retries for rate limits

        Returns:
            Gemini's response text
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=types.Content(
                        parts=[
                            types.Part(
                                file_data=types.FileData(
                                    file_uri=video_url
                                )
                            ),
                            types.Part(text=prompt)
                        ]
                    )
                )
                return response.text

            except Exception as e:
                error_str = str(e)

                # Check if this is a rate limit error
                is_rate_limit = '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower()

                if is_rate_limit:
                    # Parse retry delay from error message
                    retry_delay = None
                    if 'retry in' in error_str.lower():
                        match = re.search(r'retry in (\d+\.?\d*)s', error_str, re.IGNORECASE)
                        if match:
                            retry_delay = float(match.group(1))

                    # If this is our last attempt, raise the error
                    if attempt >= max_retries:
                        print(f"Rate limit exceeded after {max_retries} retries: {video_url}")
                        raise

                    # Wait for the retry delay (or default to exponential backoff)
                    if retry_delay:
                        wait_time = retry_delay + 2  # Add 2 seconds buffer
                        print(f"  Rate limited. Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        # Exponential backoff if no delay specified
                        wait_time = (2 ** attempt) * 10
                        print(f"  Rate limit error, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                else:
                    # Non-rate-limit error, raise immediately
                    print(f"Error analyzing video {video_url}: {e}")
                    raise

    def _get_v1_prompt(self) -> str:
        """
        Original prompt (v1) - Basic game type detection
        """
        return """
        Analyze this Mario Baseball video game and extract the following information:

        STRUCTURED DATA (required):
        1) The HUMAN PLAYER names (e.g., Dennis, Nick, Hunter, Jason, Andrew, etc.)
        2) The character team names they're using (e.g., Daisy Cupids, Mario Heroes)
        3) The final score
        4) Which PLAYER won (not team name - the human player's name)
        5) Game type: Is this a Regular Season game, Playoff, Elimination, Finals, or other tournament format?

        GAME HIGHLIGHTS:
        Summarize notable moments and gameplay:
        - Notable plays (walk-offs, grand slams, comebacks, defensive gems, close plays)
        - Game flow (was it close? blowout? back-and-forth?)
        - Turning points or momentum shifts
        - Overall game quality/excitement

        COMMENTARY HIGHLIGHTS:
        Capture memorable commentary moments:
        - Running jokes or recurring bits (e.g., specific catchphrases on certain plays)
        - Funny interactions between commentators
        - Memorable calls or reactions
        - Any callbacks or inside jokes

        Format your response exactly like this:
        Player A: [human player name]
        Team A: [character team name]
        Player B: [human player name]
        Team B: [character team name]
        Score: [A's score]-[B's score]
        Winner: [human player name who won]
        Game Type: [Regular Season/Playoff/Elimination/Finals/etc.]

        GAME SUMMARY:
        [Your game highlights and notable moments here - 2-4 sentences]

        COMMENTARY SUMMARY:
        [Your commentary highlights here - 1-3 sentences, or "None notable" if nothing stands out]

        If you cannot determine this information with confidence, respond with:
        Unable to determine: [reason]
        """

    def _get_v2_prompt(self) -> str:
        """
        Improved prompt (v2) - Better Classic 10 YERR OUT! format detection
        """
        return """
        Analyze this Mario Baseball video and extract the following information:

        FIRST - Determine if this video contains actual tournament gameplay:

        SKIP if the video is:
        - Draft/team selection content (e.g., "DRAFT DAY", "Character Steals", "Team Breakdown")
        - Analysis or prediction content (e.g., "Analysis", "Who will win", "Breakdown", "Contenders")
        - Grudge matches or exhibition games (not part of tournament standings)
        - Other non-tournament content

        If this is NOT a tournament game, respond with:
        NOT A GAME: [brief reason - e.g., "Draft video" or "Analysis content" or "Grudge match"]

        If this IS a tournament game, continue with extraction:

        STRUCTURED DATA (required):
        1) The HUMAN PLAYER names (e.g., Dennis, Nick, Hunter, Jason, Andrew, etc.)
        2) The character team names they're using (e.g., Daisy Cupids, Mario Heroes)
        3) The final score
        4) Which PLAYER won (not team name - the human player's name)
        5) Game type: Identify the specific tournament format and phase

        IMPORTANT - GAME TYPE DETECTION:

        For "Classic 10" (YERR OUT! format):
        - This tournament has a unique structure: Round-Robin → Single Elimination Game → Repeat
        - Each round consists of MULTIPLE round-robin games, followed by ONE elimination game
        - Look for these indicators:
          * Video title mentioning "Round 1", "Round 2", "Round 3", or "Finals"
          * Commentary discussing "elimination", "loser is out", or "YERR OUT"
          * Commentary mentioning round standings or who's at the bottom

        Specify the game type as one of:
        - "Classic 10 - Round 1 - Round Robin" (for regular games in Round 1)
        - "Classic 10 - Round 1 - Elimination" (for THE elimination game in Round 1)
        - "Classic 10 - Round 2 - Round Robin" (for regular games in Round 2)
        - "Classic 10 - Round 2 - Elimination" (for THE elimination game in Round 2)
        - "Classic 10 - Round 3 - Round Robin" (for regular games in Round 3)
        - "Classic 10 - Round 3 - Elimination" (for THE elimination game in Round 3)
        - "Classic 10 - Finals" (for championship games)

        For "Season 10" (traditional format):
        - Standard structure: Regular Season → Playoffs → Finals
        - Specify as:
          * "Season 10 - Regular Season"
          * "Season 10 - Playoffs"
          * "Season 10 - Finals"

        If you cannot determine the specific round or phase, use:
        - "Classic 10" (generic, will be normalized later)
        - "Season 10" (generic, will be normalized later)

        GAME HIGHLIGHTS:
        Summarize notable moments and gameplay:
        - Notable plays (walk-offs, grand slams, comebacks, defensive gems, close plays)
        - Game flow (was it close? blowout? back-and-forth?)
        - Turning points or momentum shifts
        - Overall game quality/excitement

        COMMENTARY HIGHLIGHTS:
        Capture memorable commentary moments:
        - Running jokes or recurring bits (e.g., specific catchphrases on certain plays)
        - Funny interactions between commentators
        - Memorable calls or reactions
        - Any callbacks or inside jokes

        Format your response exactly like this:
        Player A: [human player name]
        Team A: [character team name]
        Player B: [human player name]
        Team B: [character team name]
        Score: [A's score]-[B's score]
        Winner: [human player name who won]
        Game Type: [specific format from above - be as specific as possible]

        GAME SUMMARY:
        [Your game highlights and notable moments here - 2-4 sentences]

        COMMENTARY SUMMARY:
        [Your commentary highlights here - 1-3 sentences, or "None notable" if nothing stands out]

        If you cannot determine this information with confidence, respond with:
        Unable to determine: [reason]
        """

    def analyze_game_video(self, video_id: str, video_url: str = None, prompt_version: str = 'v2') -> Tuple[Optional[Dict], str]:
        """
        Analyze a baseball game video to extract game results

        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL (if None, constructs from video_id)
            prompt_version: Which prompt version to use ('v1' or 'v2')

        Returns:
            Tuple of (parsed_result_dict, raw_response_text)
            parsed_result_dict contains: team_a, team_b, score_a, score_b, winner, confidence
        """
        if not video_url:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Choose prompt based on version
        if prompt_version == 'v1':
            prompt = self._get_v1_prompt()
        else:
            prompt = self._get_v2_prompt()

        try:
            # Get response from Gemini
            raw_response = self.analyze_video_with_retry(video_url, prompt)

            # Parse the structured response
            parsed_result = self.parse_game_result(raw_response)

            # Add prompt version and model name to result
            if parsed_result:
                parsed_result['prompt_version'] = prompt_version
                parsed_result['model_name'] = self.model

            return parsed_result, raw_response

        except Exception as e:
            error_msg = f"Failed to analyze video: {str(e)}"
            print(error_msg)
            return None, error_msg

    @backoff.on_exception(
        backoff.expo,
        (exceptions.ResourceExhausted, exceptions.ServiceUnavailable, exceptions.DeadlineExceeded),
        max_tries=5,
        max_time=300
    )
    def analyze_game_videos_batch(self, video_data: List[Dict]) -> Tuple[List[Dict], str]:
        """
        Analyze multiple baseball game videos in a single request (up to 10)

        Args:
            video_data: List of dicts with 'video_id' and optional 'video_url' keys

        Returns:
            Tuple of (list of parsed_result_dicts, raw_response_text)
            Each parsed_result_dict contains: video_id, team_a, team_b, score_a, score_b, winner, confidence
        """
        if not video_data or len(video_data) == 0:
            return [], "No videos provided"

        if len(video_data) > 10:
            raise ValueError("Maximum 10 videos per batch")

        # Build the content parts
        parts = []

        # Add each video
        for video in video_data:
            video_url = video.get('video_url') or f"https://www.youtube.com/watch?v={video['video_id']}"
            parts.append(types.Part(
                file_data=types.FileData(file_uri=video_url)
            ))

        # Add the prompt
        prompt = f"""
        Analyze these {len(video_data)} baseball game videos and extract information for EACH video.

        For each video, provide:
        1) The two teams that played
        2) The final score
        3) Which team won

        Format your response for EACH video like this:

        === VIDEO 1 ===
        Team A: [name]
        Team B: [name]
        Score: [A's score]-[B's score]
        Winner: [winning team name]

        === VIDEO 2 ===
        Team A: [name]
        Team B: [name]
        Score: [A's score]-[B's score]
        Winner: [winning team name]

        (Continue for all {len(video_data)} videos)

        If you cannot determine information for a video, respond with:
        === VIDEO X ===
        Unable to determine: [reason]
        """

        parts.append(types.Part(text=prompt))

        try:
            # Make the API call
            response = self.client.models.generate_content(
                model=self.model,
                contents=types.Content(parts=parts)
            )

            raw_response = response.text

            # Parse the batch response
            results = self.parse_batch_response(raw_response, video_data)

            return results, raw_response

        except Exception as e:
            error_msg = f"Failed to analyze batch: {str(e)}"
            print(error_msg)
            # Return empty results for all videos
            return [None] * len(video_data), error_msg

    def parse_batch_response(self, response: str, video_data: List[Dict]) -> List[Dict]:
        """
        Parse batch response into individual video results

        Args:
            response: Raw text response from Gemini
            video_data: Original video data list to match results with video_ids

        Returns:
            List of dictionaries with results for each video
        """
        results = []

        # Split response by video markers
        video_sections = re.split(r'===\s*VIDEO\s+\d+\s*===', response, flags=re.IGNORECASE)

        # Skip the first split (text before first marker)
        video_sections = video_sections[1:]

        for i, section in enumerate(video_sections):
            if i >= len(video_data):
                break

            video_id = video_data[i]['video_id']

            # Parse this video's section
            parsed = self.parse_game_result(section)

            if parsed:
                parsed['video_id'] = video_id
                results.append(parsed)
            else:
                # Return None result for this video
                results.append({
                    'video_id': video_id,
                    'team_a': None,
                    'team_b': None,
                    'score_a': None,
                    'score_b': None,
                    'winner': None,
                    'confidence': 'low'
                })

        # If we didn't get results for all videos, pad with None results
        while len(results) < len(video_data):
            video_id = video_data[len(results)]['video_id']
            results.append({
                'video_id': video_id,
                'team_a': None,
                'team_b': None,
                'score_a': None,
                'score_b': None,
                'winner': None,
                'confidence': 'low'
            })

        return results

    def parse_game_result(self, response: str) -> Optional[Dict]:
        """
        Parse Gemini's structured response into a dictionary

        Args:
            response: Raw text response from Gemini

        Returns:
            Dictionary with player_a, player_b, team_a, team_b, score_a, score_b, winner, confidence
            Returns None if parsing fails
        """
        try:
            # Check for "NOT A GAME" response (non-tournament content)
            if "not a game" in response.lower():
                print(f"  Skipping non-game content: {response[:100]}")
                return None

            # Check for "Unable to determine" response
            if "unable to determine" in response.lower():
                return {
                    'player_a': None,
                    'player_b': None,
                    'team_a': None,
                    'team_b': None,
                    'score_a': None,
                    'score_b': None,
                    'winner': None,
                    'confidence': 'low'
                }

            # Extract players
            player_a_match = re.search(r'Player A:\s*(.+)', response, re.IGNORECASE)
            player_b_match = re.search(r'Player B:\s*(.+)', response, re.IGNORECASE)

            # Extract teams
            team_a_match = re.search(r'Team A:\s*(.+)', response, re.IGNORECASE)
            team_b_match = re.search(r'Team B:\s*(.+)', response, re.IGNORECASE)

            # Extract score
            score_match = re.search(r'Score:\s*(\d+)-(\d+)', response, re.IGNORECASE)

            # Extract winner
            winner_match = re.search(r'Winner:\s*(.+)', response, re.IGNORECASE)

            # Extract game type
            game_type_match = re.search(r'Game Type:\s*(.+)', response, re.IGNORECASE)

            # Extract summaries
            game_summary_match = re.search(r'GAME SUMMARY:\s*(.+?)(?=COMMENTARY SUMMARY:|$)', response, re.IGNORECASE | re.DOTALL)
            commentary_summary_match = re.search(r'COMMENTARY SUMMARY:\s*(.+)', response, re.IGNORECASE | re.DOTALL)

            if not all([player_a_match, player_b_match, score_match, winner_match]):
                # Try alternative parsing (more flexible)
                return self.flexible_parse(response)

            player_a = player_a_match.group(1).strip()
            player_b = player_b_match.group(1).strip()
            team_a = team_a_match.group(1).strip() if team_a_match else None
            team_b = team_b_match.group(1).strip() if team_b_match else None
            score_a = int(score_match.group(1))
            score_b = int(score_match.group(2))
            winner = winner_match.group(1).strip()
            game_type = game_type_match.group(1).strip() if game_type_match else "Unknown"
            game_summary = game_summary_match.group(1).strip() if game_summary_match else None
            commentary_summary = commentary_summary_match.group(1).strip() if commentary_summary_match else None

            # Determine confidence based on data completeness
            confidence = 'high'
            if not all([player_a, player_b, winner]):
                confidence = 'low'
            elif score_a == score_b:  # Tie is unusual in baseball
                confidence = 'medium'

            return {
                'player_a': player_a,
                'player_b': player_b,
                'team_a': team_a,
                'team_b': team_b,
                'score_a': score_a,
                'score_b': score_b,
                'winner': winner,
                'game_type': game_type,
                'game_summary': game_summary,
                'commentary_summary': commentary_summary,
                'confidence': confidence
            }

        except Exception as e:
            print(f"Error parsing game result: {e}")
            return None

    def flexible_parse(self, response: str) -> Optional[Dict]:
        """
        More flexible parsing for non-standard responses

        Args:
            response: Raw text response

        Returns:
            Dictionary with extracted data or None
        """
        try:
            # Look for score patterns like "X-Y", "X to Y", "X : Y"
            score_patterns = [
                r'(\d+)\s*-\s*(\d+)',
                r'(\d+)\s+to\s+(\d+)',
                r'(\d+)\s*:\s*(\d+)'
            ]

            score_a, score_b = None, None
            for pattern in score_patterns:
                match = re.search(pattern, response)
                if match:
                    score_a = int(match.group(1))
                    score_b = int(match.group(2))
                    break

            # Look for team names (capitalized words before score or "vs")
            team_pattern = r'([A-Z][a-zA-Z\s]+?)(?:\s+vs\.?|\s+versus|\s+\d+)'
            teams = re.findall(team_pattern, response)

            team_a = teams[0].strip() if len(teams) > 0 else None
            team_b = teams[1].strip() if len(teams) > 1 else None

            # Winner is team with higher score
            winner = None
            if score_a is not None and score_b is not None:
                if score_a > score_b:
                    winner = team_a
                elif score_b > score_a:
                    winner = team_b

            # Determine confidence
            confidence = 'medium' if all([team_a, team_b, score_a, score_b]) else 'low'

            return {
                'team_a': team_a,
                'team_b': team_b,
                'score_a': score_a,
                'score_b': score_b,
                'winner': winner,
                'confidence': confidence
            }

        except Exception as e:
            print(f"Flexible parsing failed: {e}")
            return None

    def test_single_video(self, video_url: str):
        """
        Test analyzer on a single video (for debugging)

        Args:
            video_url: Full YouTube video URL
        """
        print(f"Analyzing: {video_url}")
        print("-" * 60)

        video_id = self.extract_video_id(video_url)
        result, raw = self.analyze_game_video(video_id, video_url)

        print("\nRaw Response:")
        print(raw)
        print("\n" + "-" * 60)

        if result:
            print("\nParsed Result:")
            print(f"  Team A: {result['team_a']}")
            print(f"  Team B: {result['team_b']}")
            print(f"  Score: {result['score_a']}-{result['score_b']}")
            print(f"  Winner: {result['winner']}")
            print(f"  Confidence: {result['confidence']}")
        else:
            print("\nFailed to parse result")

    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # If no pattern matches, assume the URL is just the video ID
        return url


def main():
    """Test the Gemini analyzer"""
    print("Gemini Video Analyzer - Test Mode\n")

    # Check for API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("\nTo set it:")
        print("  Windows: set GEMINI_API_KEY=your_key_here")
        print("  Linux/Mac: export GEMINI_API_KEY=your_key_here")
        print("\nGet your key from: https://aistudio.google.com/")
        return

    try:
        analyzer = GeminiAnalyzer(api_key)

        print("Enter a YouTube video URL to test:")
        print("Example: https://www.youtube.com/watch?v=VIDEO_ID")
        video_url = input("> ").strip()

        if video_url:
            analyzer.test_single_video(video_url)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
