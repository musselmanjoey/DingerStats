"""
Player/Team Name Normalization
Handles inconsistent team naming from Gemini API responses
"""

# Canonical team/player mappings
# Each key is the canonical name, values are all variations that should map to it
PLAYER_MAPPINGS = {
    'Tyler (WunderBears)': [
        'tyler',
        'wunderbear',
        'wunderbears',
        'wunderbear (kritnick)',
    ],
    'Dennis (PapaDen)': [
        'dennis',
        'papaden',
        'papa den',
        'dennis papaden',
        'papaden (dennis)',
        'dennis (papaden)',
    ],
    'Hunter (Hunter Gatherers)': [
        'hunter',
        'hunter g',
        'hunter gatherers',
    ],
    'Jason (JK Jesters)': [
        'jason',
        'jk jesters',
        'jkjesters',
        'jesters',
        'jk',
    ],
    'Andrew (City Hall)': [
        'andrew',
        'city hall',
        'cityhall',
        'andrew (city hall)',
    ],
    'Nick (CritNick/Big Dog)': [
        'nick',
        'critnick',
        'kritnick',
        'crit nick',
        'big dog',
        'bigdog',
        'big dog (nick)',
    ],
    'Joey (Mr Joe)': [
        'joey',
        'mr joe',
        'mrjoe',
        'mr. joe',
    ],
}

def normalize_player_name(name):
    """
    Normalize a player/team name to its canonical form

    Args:
        name: Raw player/team name from Gemini API

    Returns:
        Canonical player name
    """
    if not name:
        return name

    # Normalize for comparison: lowercase, strip whitespace
    normalized_input = name.lower().strip()

    # Check each canonical name's variations
    for canonical, variations in PLAYER_MAPPINGS.items():
        if normalized_input in variations:
            return canonical

    # If no mapping found, return original with proper capitalization
    return name.strip()


def get_all_canonical_names():
    """Get list of all canonical player names"""
    return list(PLAYER_MAPPINGS.keys())


def get_variations(canonical_name):
    """Get all variations for a canonical name"""
    return PLAYER_MAPPINGS.get(canonical_name, [])


# For debugging - show what names would map to
if __name__ == '__main__':
    test_names = [
        'Tyler',
        'WunderBear',
        'WunderBear (KritNick)',
        'Dennis',
        'PapaDen',
        'Hunter',
        'Hunter G',
        'Jason',
        'City Hall',
        'Andrew',
        'Big Dog',
        'Nick',
        'CritNick',
    ]

    print('Name normalization mapping:')
    for name in test_names:
        normalized = normalize_player_name(name)
        print(f'  {name:25} -> {normalized}')
