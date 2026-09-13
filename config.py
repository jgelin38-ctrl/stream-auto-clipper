import os
from dotenv import load_dotenv

load_dotenv()

# Streaming platform configuration - SUPPORT MULTIPLE STREAMS
STREAMER_URLS = [
    os.getenv('STREAMER_URL_1', ''),  # e.g., https://www.twitch.tv/username1
    os.getenv('STREAMER_URL_2', ''),  # e.g., https://www.twitch.tv/username2
]

# Filter out empty URLs
STREAMER_URLS = [url for url in STREAMER_URLS if url.strip()]

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

# Multi-threading configuration
MAX_CONCURRENT_STREAMS = int(os.getenv('MAX_CONCURRENT_STREAMS', '2'))

# Chat-based clip detection configuration
ENABLE_CHAT_DETECTION = os.getenv('ENABLE_CHAT_DETECTION', 'true').lower() == 'true'
CHAT_SPIKE_THRESHOLD = int(os.getenv('CHAT_SPIKE_THRESHOLD', '20'))  # messages per second
CHAT_WINDOW_SIZE = int(os.getenv('CHAT_WINDOW_SIZE', '5'))  # seconds to track chat activity
MIN_CHAT_MESSAGES = int(os.getenv('MIN_CHAT_MESSAGES', '50'))  # minimum messages to trigger clip
CLIP_BEFORE_SPIKE = int(os.getenv('CLIP_BEFORE_SPIKE', '10'))  # seconds before spike to include
CLIP_AFTER_SPIKE = int(os.getenv('CLIP_AFTER_SPIKE', '30'))  # seconds after spike to include

# Emote-based detection (keywords that trigger clips)
EMOTES_TO_TRACK = os.getenv('EMOTES_TO_TRACK', 'PogU,KEKW,monkaS,OMEGALUL,Pog').split(',')
EMOTE_TRIGGER_COUNT = int(os.getenv('EMOTE_TRIGGER_COUNT', '10'))  # emotes needed in window to trigger
