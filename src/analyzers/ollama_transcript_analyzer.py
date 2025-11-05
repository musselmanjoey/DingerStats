"""
Ollama Transcript Analyzer for DingerStats
Uses local Ollama models to analyze YouTube transcripts for game data
Free alternative to Gemini API
"""

import requests
import json
from youtube_transcript_api import YouTubeTranscriptApi as TranscriptAPI
from typing import Dict, Optional, Tuple


class OllamaTranscriptAnalyzer:
    def __init__(self, model: str = "llama3.2:3b", ollama_url: str = "http://localhost:11434"):
        """
        Initialize Ollama analyzer

        Args:
            model: Ollama model to use (default: llama3.2:3b - fast and good for structured tasks)
            ollama_url: Ollama API endpoint
        """
        self.model = model
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"

    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch YouTube transcript for a video

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text or None if unavailable
        """
        try:
            # Create an instance and fetch transcript
            api = TranscriptAPI()
            transcript_list = api.fetch(video_id)

            # Combine all transcript entries into one text
            full_transcript = " ".join([entry.text for entry in transcript_list])

            return full_transcript

        except Exception as e:
            print(f"  Failed to fetch transcript: {e}")
            return None

    def analyze_with_ollama(self, prompt: str, transcript: str) -> Optional[str]:
        """
        Send transcript to Ollama for analysis

        Args:
            prompt: System prompt for analysis
            transcript: Video transcript text

        Returns:
            Ollama's response or None if failed
        """
        try:
            full_prompt = f"{prompt}\n\nTranscript:\n{transcript}\n\nAnalysis:"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1  # Low temperature for consistent structured output
                }
            }

            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=300  # 5 minute timeout for local processing
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"  Ollama error: {response.status_code}")
                return None

        except Exception as e:
            print(f"  Ollama request failed: {e}")
            return None

    def get_analysis_prompt(self) -> str:
        """
        Get the structured prompt for game analysis (v2 - improved game type detection)
        """
        return """You are analyzing a Mario Baseball tournament video transcript.

FIRST - Determine if this transcript contains actual tournament gameplay:

SKIP if the video is:
- Draft/team selection content (e.g., "DRAFT DAY", "Character Steals", "Team Breakdown")
- Analysis or prediction content (e.g., "Analysis", "Who will win", "Breakdown", "Contenders")
- Grudge matches or exhibition games (not part of tournament standings)
- Other non-tournament content

If this is NOT a tournament game, return:
{"not_a_game": true, "reason": "brief explanation"}

If this IS a tournament game, extract the following in JSON format:

{
  "player_a": "First HUMAN player's name (e.g., Dennis, Nick, Hunter, Jason, Andrew)",
  "player_b": "Second HUMAN player's name",
  "score_a": "Final score for player A (number only)",
  "score_b": "Final score for player B (number only)",
  "winner": "HUMAN player name who won (not team name)",
  "game_type": "Specific tournament format and phase - see rules below",
  "confidence": "high/medium/low based on clarity of information"
}

GAME TYPE DETECTION RULES:

For "Classic 10" (YERR OUT! format):
- This tournament has: Round-Robin → Single Elimination Game → Repeat
- Each round has MULTIPLE round-robin games, then ONE elimination game
- Look for indicators: "Round 1", "Round 2", "Round 3", "Finals", "elimination", "loser is out", "YERR OUT"

Specify game_type as:
- "Classic 10 - Round 1 - Round Robin" (regular games in Round 1)
- "Classic 10 - Round 1 - Elimination" (THE elimination game in Round 1)
- "Classic 10 - Round 2 - Round Robin" (regular games in Round 2)
- "Classic 10 - Round 2 - Elimination" (THE elimination game in Round 2)
- "Classic 10 - Round 3 - Round Robin" (regular games in Round 3)
- "Classic 10 - Round 3 - Elimination" (THE elimination game in Round 3)
- "Classic 10 - Finals" (championship games)

For "Season 10" (traditional format):
- "Season 10 - Regular Season"
- "Season 10 - Playoffs"
- "Season 10 - Finals"

If unsure of specific round: use "Classic 10" or "Season 10" (generic)

IMPORTANT:
- Return ONLY valid JSON, no other text
- Focus on gameplay commentary to find scores and player names
- Look for phrases like "wins", "final score", "takes it", "victory"

Transcript follows below:"""

    def analyze_game_video(self, video_id: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Analyze a game video using its transcript

        Args:
            video_id: YouTube video ID

        Returns:
            Tuple of (parsed_result_dict, raw_response_string)
        """
        # Get transcript
        print(f"  Fetching transcript...")
        transcript = self.get_transcript(video_id)

        if not transcript:
            return None, "No transcript available"

        print(f"  Transcript length: {len(transcript)} chars")

        # Truncate if too long (Ollama context limits)
        # Keep BEGINNING (intro with players/commentators) and END (final score/winner)
        MAX_LENGTH = 8000
        if len(transcript) > MAX_LENGTH:
            # Take first 4000 chars (intro) and last 4000 chars (ending/score)
            beginning = transcript[:4000]
            ending = transcript[-4000:]
            transcript = beginning + "\n\n...[middle content truncated]...\n\n" + ending
            print(f"  Truncated to {MAX_LENGTH} chars (beginning + ending)")

        # Analyze with Ollama
        print(f"  Analyzing with Ollama ({self.model})...")
        prompt = self.get_analysis_prompt()
        response = self.analyze_with_ollama(prompt, transcript)

        if not response:
            return None, "Ollama analysis failed"

        # Parse response
        result = self.parse_response(response)

        return result, response

    def parse_response(self, response: str) -> Optional[Dict]:
        """
        Parse Ollama's JSON response into a dictionary
        """
        try:
            # Try to find JSON in response
            # Sometimes models add extra text, so look for { }
            start = response.find('{')
            end = response.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                # Check if it's a non-game
                if data.get('not_a_game'):
                    print(f"  Not a game: {data.get('reason')}")
                    return None

                return data
            else:
                print(f"  Could not find JSON in response")
                return None

        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            print(f"  Response: {response[:200]}")
            return None
        except Exception as e:
            print(f"  Parse error: {e}")
            return None


def test_analyzer():
    """Test the analyzer with a known video"""
    analyzer = OllamaTranscriptAnalyzer()

    # Test with a Classic 10 video
    test_video_id = "WbY_IjNfUsQ"  # "The best draft pick of the Mario Baseball season"

    print(f"Testing Ollama Transcript Analyzer")
    print(f"Video ID: {test_video_id}")
    print(f"Model: {analyzer.model}")
    print()

    result, raw = analyzer.analyze_game_video(test_video_id)

    if result:
        print("\nExtracted Data:")
        print(json.dumps(result, indent=2))
    else:
        print("\nFailed to extract data")

    print("\nRaw Response:")
    print(raw[:500] if raw else "No response")


if __name__ == '__main__':
    test_analyzer()
