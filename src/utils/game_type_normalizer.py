"""
Game Type Normalization
Handles inconsistent game type naming from Gemini API responses
"""

# Game type mappings
# Key: canonical game type, Value: list of variations that map to it
#
# Classic 10 uses "YERR OUT!" format:
#   - Round-Robin → Elimination Game → Repeat until Finals
#   - Phases: Round 1, Round 2, Round 3, Finals
GAME_TYPE_MAPPINGS = {
    # Classic 10 - Round 1
    'Classic 10 - Round 1': [
        # v1 prompt variations
        'classic 10',
        'classic',  # AI often just says "Classic" for Classic 10
        'regular season (classic 10)',
        'regular season',  # Generic "Regular Season" in Classic 10 is Round-Robin
        'classic 10 (tournament format)',
        'classic 10 (tournament)',
        'classic 10 (tournament round, but not explicitly playoffs, elimination or finals)',
        # v2 prompt variations
        'classic 10 - round 1 - round robin',
        'classic 10 - round 1 - elimination',
    ],
    # Classic 10 - Round 2
    'Classic 10 - Round 2': [
        # v1 prompt variations
        'classic 10 playoffs',
        'playoff, round two',
        'other (round 3 - dinger city classic 10)',
        # v2 prompt variations
        'classic 10 - round 2 - round robin',
        'classic 10 - round 2 - elimination',
    ],
    # Classic 10 - Round 3
    'Classic 10 - Round 3': [
        # v1 prompt variations
        'elimination',  # Generic "Elimination" games
        'elimination (determined in video)',
        'elimination (from classic 10 tournament)',
        'elimination (classic 10 round 3 game)',
        # v2 prompt variations
        'classic 10 - round 3 - round robin',
        'classic 10 - round 3 - elimination',
    ],
    # Classic 10 - Finals
    'Classic 10 - Finals': [
        # v1 prompt variations
        'finals',
        'classic 10 finals',
        'tournament format',
        # v2 prompt variations
        'classic 10 - finals',
    ],
    # For Seasons (traditional format)
    'Season 10 - Regular Season': [
        'season 10',
        'season 10 regular season',
        'season 10 - regular season',
    ],
    'Season 10 - Playoffs': [
        'season 10 playoffs',
        'season 10 - playoffs',
    ],
    'Season 10 - Finals': [
        'season 10 finals',
        'season 10 - finals',
    ],
}

def normalize_game_type(game_type):
    """
    Normalize a game type to its canonical form

    Args:
        game_type: Raw game type from Gemini API

    Returns:
        Canonical game type string
    """
    if not game_type:
        return 'Unknown'

    # Normalize for comparison: lowercase, strip whitespace
    normalized_input = game_type.lower().strip()

    # Check each canonical type's variations
    for canonical, variations in GAME_TYPE_MAPPINGS.items():
        if normalized_input in variations:
            return canonical

    # If no mapping found, return original with proper capitalization
    return game_type.strip()


def get_season_from_game_type(game_type):
    """
    Extract season identifier from game type

    Returns:
        Season identifier like "Classic 10", "Classic", etc.
    """
    canonical = normalize_game_type(game_type)

    # Extract the season part (before the dash)
    if ' - ' in canonical:
        return canonical.split(' - ')[0]

    return canonical


def get_phase_from_game_type(game_type):
    """
    Extract phase from game type (Regular Season, Playoffs, Finals, etc.)

    Returns:
        Phase identifier like "Regular Season", "Playoffs", "Finals", etc.
    """
    canonical = normalize_game_type(game_type)

    # Extract the phase part (after the dash)
    if ' - ' in canonical:
        return canonical.split(' - ')[1]

    return 'Regular Season'


def get_all_seasons():
    """Get list of all unique seasons"""
    seasons = set()
    for canonical in GAME_TYPE_MAPPINGS.keys():
        seasons.add(get_season_from_game_type(canonical))
    return sorted(list(seasons))


# For debugging
if __name__ == '__main__':
    test_types = [
        'Classic 10',
        'CLASSIC 10',
        'Regular Season (Classic 10)',
        'Classic 10 (Tournament Format)',
        'Elimination (from Classic 10 tournament)',
        'Finals',
        'Classic',
        'Regular Season',
        'Elimination',
        'Playoff, Round Two',
    ]

    print('Game type normalization mapping:')
    for gt in test_types:
        normalized = normalize_game_type(gt)
        season = get_season_from_game_type(gt)
        phase = get_phase_from_game_type(gt)
        print(f'  {gt:45} -> {normalized:35} (Season: {season}, Phase: {phase})')
