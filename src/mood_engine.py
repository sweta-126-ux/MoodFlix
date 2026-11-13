
MOOD_PROFILES = {
    "Happy": {
        "genres": ["Comedy", "Animation", "Adventure"],
        "description": "Feel-good stories to keep your happiness going."
    },
    "Sad": {
        "genres": ["Drama", "Romance", "Family"],
        "description": "Comforting stories for emotional moments."
    },
    "Romantic": {
        "genres": ["Romance", "Drama", "Comedy"],
        "description": "Stories filled with love and connection."
    },
    "Angry": {
        "genres": ["Action", "Thriller", "Adventure"],
        "description": "High-energy stories to match your mood."
    },
    "Bored": {
        "genres": ["Mystery", "Thriller", "Science Fiction"],
        "description": "Interesting stories to grab your attention."
    },
    "Curious": {
        "genres": ["Mystery", "Documentary", "Science Fiction"],
        "description": "Stories that make you think."
    },
    "Relaxed": {
        "genres": ["Family", "Comedy", "Fantasy"],
        "description": "Easygoing entertainment for a peaceful day."
    },
    "Adventurous": {
        "genres": ["Adventure", "Action", "Fantasy"],
        "description": "Explore exciting new worlds."
    }
}

def get_mood_profile(mood):
    """Return the recommendation profile for a selected mood."""

    return MOOD_PROFILES.get(
        mood,
        {
            "genres": [],
            "description": "Discover something new."
        }
    )