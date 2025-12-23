import re
from typing import Optional


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract YouTube playlist ID from URL"""
    pattern = r'(?:list=)([^&\n?#]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None


def is_valid_youtube_url(url: str) -> bool:
    """Validate if URL is a valid YouTube URL"""
    return bool(extract_video_id(url) or extract_playlist_id(url))