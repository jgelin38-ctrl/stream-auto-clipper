import logging
import threading
from collections import deque
from datetime import datetime
import os
from config import (
    CHAT_WINDOW_SIZE, CHAT_SPIKE_THRESHOLD, MIN_CHAT_MESSAGES,
    CLIP_BEFORE_SPIKE, CLIP_AFTER_SPIKE, EMOTES_TO_TRACK, EMOTE_TRIGGER_COUNT,
    LOG_DIR
)

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'chat_detector.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatSpike:
    """Represents a detected chat spike event"""
    def __init__(self, timestamp, message_count, emote_count, spike_type):
        self.timestamp = timestamp
        self.message_count = message_count
        self.emote_count = emote_count
        self.spike_type = spike_type  # 'spike' or 'emote'
        self.clip_start = max(0, timestamp - CLIP_BEFORE_SPIKE)
        self.clip_end = timestamp + CLIP_AFTER_SPIKE

class ChatDetector:
    """Detects high interaction moments in chat"""
    
    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.message_buffer = deque(maxlen=CHAT_WINDOW_SIZE * 60)  # Store messages for window
        self.timestamps = deque(maxlen=CHAT_WINDOW_SIZE * 60)
        self.detected_spikes = []
        self.lock = threading.Lock()
        self.current_time = None
        
    def add_message(self, message_text, timestamp=None):
        """Add a chat message and check for spikes"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with self.lock:
            self.current_time = timestamp
            self.message_buffer.append(message_text)
            self.timestamps.append(timestamp)
            
            # Check for chat spike
            spike = self._check_for_spike(timestamp)
            if spike:
                self.detected_spikes.append(spike)
                logger.info(
                    f'[{self.channel_name}] Chat spike detected! '
                    f'Messages: {spike.message_count}, '
                    f'Clip: {spike.clip_start}s - {spike.clip_end}s'
                )
                return spike
            
            # Check for emote spike
            emote_spike = self._check_for_emote_spike(message_text, timestamp)
            if emote_spike:
                self.detected_spikes.append(emote_spike)
                logger.info(
                    f'[{self.channel_name}] Emote spike detected! '
                    f'Emotes: {emote_spike.emote_count}, '
                    f'Clip: {emote_spike.clip_start}s - {emote_spike.clip_end}s'
                )
                return emote_spike
        
        return None
    
    def _check_for_spike(self, current_timestamp):
        """Check if there's a spike in chat activity"""
        # Count messages in the last CHAT_WINDOW_SIZE seconds
        window_start = current_timestamp.timestamp() - CHAT_WINDOW_SIZE
        
        messages_in_window = sum(
            1 for ts in self.timestamps
            if ts.timestamp() >= window_start
        )
        
        # Check if spike threshold is exceeded
        if messages_in_window >= MIN_CHAT_MESSAGES:
            msgs_per_second = messages_in_window / CHAT_WINDOW_SIZE
            if msgs_per_second >= CHAT_SPIKE_THRESHOLD:
                # Convert to streaming seconds (approximate)
                spike_time = int(current_timestamp.timestamp())
                return ChatSpike(
                    spike_time,
                    messages_in_window,
                    0,
                    'spike'
                )
        
        return None
    
    def _check_for_emote_spike(self, message_text, current_timestamp):
        """Check if there's a spike in emote usage"""
        # Count emotes in recent messages
        window_start = current_timestamp.timestamp() - CHAT_WINDOW_SIZE
        emote_count = 0
        
        for msg in self.message_buffer:
            for emote in EMOTES_TO_TRACK:
                emote_count += msg.upper().count(emote.upper())
        
        # Check if emote threshold is exceeded
        if emote_count >= EMOTE_TRIGGER_COUNT:
            spike_time = int(current_timestamp.timestamp())
            return ChatSpike(
                spike_time,
                len(self.message_buffer),
                emote_count,
                'emote'
            )
        
        return None
    
    def get_spikes_in_range(self, start_time, end_time):
        """Get all detected spikes within a time range"""
        with self.lock:
            return [
                spike for spike in self.detected_spikes
                if start_time <= spike.timestamp <= end_time
            ]
    
    def get_latest_spike(self):
        """Get the most recent detected spike"""
        with self.lock:
            return self.detected_spikes[-1] if self.detected_spikes else None
    
    def clear_spikes(self):
        """Clear detected spikes (after processing)"""
        with self.lock:
            self.detected_spikes.clear()
    
    def get_stats(self):
        """Get chat detector statistics"""
        with self.lock:
            return {
                'channel': self.channel_name,
                'total_messages': len(self.message_buffer),
                'total_spikes_detected': len(self.detected_spikes),
                'last_spike': self.detected_spikes[-1] if self.detected_spikes else None
            }
