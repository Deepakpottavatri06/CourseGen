from better_profanity import profanity

def is_profane(text: str) -> bool:
    """Check if the text contains profane words."""
    return profanity.contains_profanity(text)