import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import os
from config import MAX_CONCURRENT_STREAMS, LOG_DIR, STREAMER_URLS, ENABLE_CHAT_DETECTION
from stream_monitor import StreamMonitor
from clip_generator import ClipGenerator
from twitch_chat_listener import TwitchChatListener

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'multi_stream.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StreamSession:
    """Manages a single stream session with monitoring, recording, and chat detection"""
    
    def __init__(self, streamer_url, output_dir):
        self.streamer_url = streamer_url
        self.channel_name = self._extract_channel_name(streamer_url)
        self.output_dir = os.path.join(output_dir, self.channel_name)
        self.monitor = StreamMonitor(streamer_url, self.output_dir)
        self.clipper = ClipGenerator()
        self.chat_listener = None
        self.recording_file = None
        self.is_recording = False
        
        # Initialize chat detection if enabled
        if ENABLE_CHAT_DETECTION and 'twitch' in streamer_url.lower():
            self.chat_listener = TwitchChatListener(self.channel_name)
    
    def _extract_channel_name(self, url):
        """Extract channel name from URL"""
        # Handle URLs like https://www.twitch.tv/username or https://twitch.tv/username
        parts = url.rstrip('/').split('/')
        return parts[-1].lower()
    
    def start(self):
        """Start monitoring this stream"""
        logger.info(f'Starting stream session for: {self.channel_name}')
        
        # Start chat listener if available
        if self.chat_listener:
            logger.info(f'Starting chat listener for {self.channel_name}')
            self.chat_listener.start_listening()
    
    def stop(self):
        """Stop monitoring this stream"""
        logger.info(f'Stopping stream session for: {self.channel_name}')
        
        if self.is_recording:
            self.monitor.stop_recording()
            self.is_recording = False
        
        if self.chat_listener:
            self.chat_listener.stop_listening()
    
    def check_and_record(self):
        """Check if stream is live and handle recording"""
        is_live = self.monitor.is_streaming()
        
        if is_live and not self.is_recording:
            logger.info(f'{self.channel_name}: Stream detected! Starting recording...')
            self.recording_file = self.monitor.start_recording()
            self.is_recording = True
            return 'started'
        
        elif not is_live and self.is_recording:
            logger.info(f'{self.channel_name}: Stream went offline. Stopping recording...')
            self.monitor.stop_recording()
            self.is_recording = False
            
            # Process clips with chat detection if available
            if self.recording_file:
                self._process_recording()
            
            return 'stopped'
        
        elif is_live and self.is_recording:
            return 'recording'
        
        else:
            return 'offline'
    
    def _process_recording(self):
        """Process the recorded file and generate clips"""
        try:
            logger.info(f'{self.channel_name}: Processing recording...')
            
            # Get detected chat spikes if available
            spikes = []
            if self.chat_listener:
                spikes = self.chat_listener.get_detector().detected_spikes
                logger.info(f'{self.channel_name}: Detected {len(spikes)} chat spikes')
            
            clips_dir = os.path.join(self.output_dir, 'clips')
            
            # If spikes detected, create targeted clips
            if spikes:
                clips = self._generate_clips_from_spikes(spikes, clips_dir)
                logger.info(f'{self.channel_name}: Generated {len(clips)} spike-based clips')
            else:
                # Generate regular 80-second clips
                clips = self.clipper.generate_clips(
                    self.recording_file,
                    clips_dir
                )
                logger.info(f'{self.channel_name}: Generated {len(clips)} regular clips')
            
            # Clear detected spikes after processing
            if self.chat_listener:
                self.chat_listener.get_detector().clear_spikes()
                
        except Exception as e:
            logger.error(f'{self.channel_name}: Error processing recording: {e}')
    
    def _generate_clips_from_spikes(self, spikes, output_dir):
        """Generate clips based on detected chat spikes"""
        clips = []
        os.makedirs(output_dir, exist_ok=True)
        
        for i, spike in enumerate(spikes):
            try:
                logger.info(
                    f'{self.channel_name}: Creating spike clip {i+1} '
                    f'({spike.clip_start}s - {spike.clip_end}s) '
                    f'Type: {spike.spike_type}'
                )
                
                clip_path = os.path.join(
                    output_dir,
                    f'{self.channel_name}_spike_{i+1:02d}_{spike.spike_type}.mp4'
                )
                
                # Use ffmpeg to extract clip based on spike timestamps
                clip = self.clipper.extract_clip(
                    self.recording_file,
                    clip_path,
                    spike.clip_start,
                    spike.clip_end
                )
                
                if clip:
                    clips.append(clip)
                    
            except Exception as e:
                logger.error(f'{self.channel_name}: Error creating spike clip {i+1}: {e}')
        
        return clips
    
    def get_stats(self):
        """Get session statistics"""
        stats = {
            'channel': self.channel_name,
            'url': self.streamer_url,
            'recording': self.is_recording,
            'output_dir': self.output_dir
        }
        
        if self.chat_listener:
            stats['chat'] = self.chat_listener.get_stats()
        
        return stats


class MultiStreamManager:
    """Manages multiple concurrent stream monitoring sessions"""
    
    def __init__(self, streamer_urls, output_dir):
        self.streamer_urls = streamer_urls
        self.output_dir = output_dir
        self.sessions = []
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_STREAMS)
        self.running = False
    
    def start(self):
        """Start monitoring all streams"""
        logger.info('='*60)
        logger.info('Multi-Stream Auto-Clipper Started')
        logger.info(f'Monitoring {len(self.streamer_urls)} streams')
        logger.info('='*60)
        
        # Create session for each URL
        for url in self.streamer_urls:
            session = StreamSession(url, self.output_dir)
            self.sessions.append(session)
            session.start()
        
        self.running = True
    
    def stop(self):
        """Stop monitoring all streams"""
        logger.info('Stopping Multi-Stream Manager...')
        self.running = False
        
        for session in self.sessions:
            session.stop()
        
        self.executor.shutdown(wait=True)
    
    def monitor_all(self, interval=30):
        """Main monitoring loop for all streams"""
        import time
        
        try:
            while self.running:
                for session in self.sessions:
                    try:
                        status = session.check_and_record()
                        stats = session.get_stats()
                        logger.debug(f'Status update - {stats["channel"]}: {status}')
                    except Exception as e:
                        logger.error(f'Error checking session {session.channel_name}: {e}')
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info('Shutting down...')
            self.stop()
        except Exception as e:
            logger.error(f'Monitor loop error: {e}')
            self.stop()
    
    def get_all_stats(self):
        """Get statistics for all sessions"""
        return [session.get_stats() for session in self.sessions]
