"""
Central configuration for DingerStats
All scripts and modules should import from here to avoid duplication
"""
import os
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = os.getenv('DINGERSTATS_DB_PATH', str(PROJECT_ROOT / 'database' / 'dingerstats.db'))

# YouTube playlists
PLAYLISTS = {
    'classic10': 'PL4KAbBInKJ-x2Thksr-E8xKnpdElGeeqF',
    'season10': 'PL4KAbBInKJ-wULDmMsXHk6lmNdN4WpKk2',
}

# API configuration
API_PORT_MAIN = int(os.getenv('API_PORT_MAIN', 5000))
API_PORT_PROGRESS = int(os.getenv('API_PORT_PROGRESS', 5001))

# Analyzer defaults
DEFAULT_GEMINI_MODEL = 'gemini-2.0-flash-exp'
DEFAULT_OLLAMA_MODEL = 'llama3.2:1b'
DEFAULT_OLLAMA_URL = 'http://localhost:11434'

# Prompt versions available
PROMPT_VERSIONS = ['v1', 'v2']

# Analyzer types
ANALYZER_TYPES = ['gemini_visual', 'ollama_transcript']

# API Keys (loaded from environment)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
