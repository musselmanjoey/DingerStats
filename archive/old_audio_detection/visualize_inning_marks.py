"""
Visualize the corrected inning transition timestamps for verification.
"""

import matplotlib.pyplot as plt
import numpy as np

def visualize_inning_marks():
    """
    Create a timeline chart showing all inning transitions for verification.
    """
    print("Visualizing Inning Transition Marks")
    print("=" * 40)
    
    # All inning transitions with your clarifications
    transitions = [
        {"time_mm_ss": "2:28", "time_seconds": 2*60 + 28, "description": "Top of 1st to Bottom of 1st"},
        {"time_mm_ss": "3:19", "time_seconds": 3*60 + 19, "description": "Bottom of 1st to Top of 2nd"}, 
        {"time_mm_ss": "4:03", "time_seconds": 4*60 + 3,  "description": "Top of 2nd to Bottom of 2nd"},
        {"time_mm_ss": "5:14", "time_seconds": 5*60 + 14, "description": "Bottom of 2nd to Top of 3rd"},
        {"time_mm_ss": "7:34", "time_seconds": 7*60 + 34, "description": "Top of 3rd to Bottom of 3rd"},
    ]
    
    print("Your identified inning transitions:")
    print("-" * 50)
    for i, t in enumerate(transitions):
        print(f"{i+1}. {t['time_mm_ss']} ({t['time_seconds']:3d}s) - {t['description']}")
    
    # Create timeline visualization
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Timeline from 0 to 10 minutes
    timeline_end = 10 * 60  # 10 minutes in seconds
    
    # Draw timeline
    ax.plot([0, timeline_end], [0, 0], 'k-', linewidth=2, alpha=0.3)
    
    # Mark inning transitions
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    
    for i, transition in enumerate(transitions):
        time_sec = transition['time_seconds']
        time_str = transition['time_mm_ss']
        desc = transition['description']
        
        # Vertical line for each transition
        ax.axvline(x=time_sec, color=colors[i], linewidth=3, alpha=0.8)
        
        # Label above the line
        ax.text(time_sec, 0.5, f"{time_str}\n{desc}", 
                rotation=45, ha='left', va='bottom', 
                fontsize=10, color=colors[i], weight='bold')
        
        # Mark on timeline
        ax.plot(time_sec, 0, 'o', color=colors[i], markersize=12, markeredgecolor='black')
    
    # Format chart
    ax.set_xlim(0, timeline_end)
    ax.set_ylim(-0.2, 1.5)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_title('Mario Baseball Inning Transitions - Manual Identification\n(Each sound lasts ~2 seconds)', 
                fontsize=14, weight='bold')
    
    # Add minute markers
    for minute in range(0, 11):
        minute_sec = minute * 60
        ax.axvline(x=minute_sec, color='gray', linestyle='--', alpha=0.3)
        ax.text(minute_sec, -0.1, f"{minute}:00", ha='center', va='top', fontsize=9, color='gray')
    
    # Remove y-axis (not needed for timeline)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    plt.tight_layout()
    
    # Save the chart
    chart_file = "inning_transitions_timeline.png"
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"\n[SAVED] Timeline chart: {chart_file}")
    
    plt.show()
    
    # Summary for verification
    print(f"\nSUMMARY FOR VERIFICATION:")
    print(f"Total inning transitions: {len(transitions)}")
    print(f"Time span: {transitions[0]['time_mm_ss']} to {transitions[-1]['time_mm_ss']}")
    print(f"Timestamps in seconds: {[t['time_seconds'] for t in transitions]}")
    
    return transitions

if __name__ == "__main__":
    transitions = visualize_inning_marks()
    
    print(f"\nDoes this timeline correctly show your inning transition marks?")
    print(f"Each mark represents where the ~2-second inning sound occurs.")