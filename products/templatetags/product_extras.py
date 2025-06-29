from django import template
import re

register = template.Library()

@register.filter(name='embed_youtube_url')
def embed_youtube_url(value):
    if not isinstance(value, str):
        return '' # Return empty string or original value if not a string
    # Converts youtube.com/watch?v=ID to youtube.com/embed/ID
    # Also handles youtu.be/ID and youtube.com/embed/ID (idempotent)
    # Handles URLs with extra parameters like ?t=1s
    
    # Regex to find YouTube ID from various URL formats
    regex_patterns = [
        r"(?:https|http)://(?:www\.)?youtube\.com/(?:embed/|watch\?v=|v/|shorts/|live/)([\w-]+)(?:\?.*)?",
        r"(?:https|http)://(?:www\.)?youtu\.be/([\w-]+)(?:\?.*)?"
    ]
    
    video_id = None
    for pattern in regex_patterns:
        match = re.search(pattern, value)
        if match:
            video_id = match.group(1)
            break
            
    if video_id:
        return f"https://www.youtube.com/embed/{video_id}"
    
    return value # Return original if not a recognized YouTube URL or if ID extraction fails 