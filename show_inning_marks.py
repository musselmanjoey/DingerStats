"""
Show the corrected inning transition timestamps for verification.
"""

def show_inning_marks():
    """
    Display all inning transitions in a clear format for verification.
    """
    print("Your Corrected Inning Transition Marks")
    print("=" * 50)
    
    # All 5 inning transitions as you clarified
    transitions = [
        {"time_mm_ss": "2:28", "time_seconds": 2*60 + 28, "description": "Top of 1st to Bottom of 1st"},
        {"time_mm_ss": "3:19", "time_seconds": 3*60 + 19, "description": "Bottom of 1st to Top of 2nd"}, 
        {"time_mm_ss": "4:03", "time_seconds": 4*60 + 3,  "description": "Top of 2nd to Bottom of 2nd"},
        {"time_mm_ss": "5:14", "time_seconds": 5*60 + 14, "description": "Bottom of 2nd to Top of 3rd"},
        {"time_mm_ss": "7:34", "time_seconds": 7*60 + 34, "description": "Top of 3rd to Bottom of 3rd"},
    ]
    
    print("Transition #  |  Time   | Seconds |  Inning Change")
    print("-" * 55)
    
    for i, t in enumerate(transitions, 1):
        print(f"     {i}       |  {t['time_mm_ss']}  |   {t['time_seconds']:3d}   | {t['description']}")
    
    print("\nKey Details:")
    print("- Each transition sound lasts approximately 2 seconds")
    print("- These mark the audio cue when innings change") 
    print("- Total of 5 transition sounds in the first ~8 minutes")
    
    print(f"\nOriginal vs Corrected:")
    print("ORIGINAL (what I had): Only 3 marks at 2:28, 4:03, 7:34")
    print("CORRECTED (what you clarified): 5 marks including 3:19 and 5:14")
    
    print(f"\nFor pattern matching, we now need to:")
    print("1. Extract all 5 examples instead of just 3")
    print("2. Build a better reference pattern")
    print("3. Test against all 5 known locations")
    
    return transitions

if __name__ == "__main__":
    transitions = show_inning_marks()
    
    print(f"\nDoes this correctly represent your inning transition marks?")
    print(f"Please confirm before we update the pattern matching system.")