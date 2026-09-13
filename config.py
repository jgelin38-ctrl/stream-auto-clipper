import os
from dotenv import load_dotenv

load_dotenv()

# Streaming platform configuration
STREAMER_URL = os.getenv('STREAMER_URL', '')  # e.g., https://www.twitch.tv/username
CLIP_DURATION = 80  # seconds
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './clips')
LOG_DIR = os.getenv('LOG_DIR', './logs')

# FFmpeg configuration
FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')

# Twitch API configuration (optional, for enhanced features)
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID', '')
TWITCH_ACCESS_TOKEN = os.getenv('TWITCH_ACCESS_TOKEN', '')

# Output quality
QUALITY = os.getenv('QUALITY', 'best')  # 'best', '1080p60', '720p60', etc.

# Enable/disable features
UPLOAD_TO_YOUTUBE = os.getenv('UPLOAD_TO_YOUTUBE', 'false').lower() == 'true'
SAVE_LOCALLY = os.getenv('SAVE_LOCALLY', 'true').lower() == 'true'
