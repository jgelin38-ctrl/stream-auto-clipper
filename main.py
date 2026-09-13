import time
import logging
import os
from config import STREAMER_URL, OUTPUT_DIR, LOG_DIR, CLIP_DURATION
from stream_monitor import StreamMonitor
from clip_generator import ClipGenerator

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'main.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StreamClipper:
    """Main orchestrator for automatic stream clipping"""
    
    def __init__(self, streamer_url, output_dir):
        self.streamer_url = streamer_url
        self.output_dir = output_dir
        self.monitor = StreamMonitor(streamer_url, output_dir)
        self.clipper = ClipGenerator(CLIP_DURATION)
        self.recording_file = None
        
    def run(self):
        """Main loop for monitoring and clipping"""
        logger.info('='*50)
        logger.info('Stream Auto-Clipper Started')
        logger.info(f'Streamer URL: {self.streamer_url}')
        logger.info(f'Clip Duration: {CLIP_DURATION} seconds')
        logger.info(f'Output Directory: {self.output_dir}')
        logger.info('='*50)
        
        is_recording = False
        
        try:
            while True:
                # Check if stream is live
                if self.monitor.is_streaming():
                    if not is_recording:
                        logger.info('Stream detected! Starting recording...')
                        self.recording_file = self.monitor.start_recording()
                        is_recording = True
                    else:
                        logger.info('Stream is live and recording...')
                else:
                    if is_recording:
                        logger.info('Stream went offline. Stopping recording...')
                        self.monitor.stop_recording()
                        is_recording = False
                        
                        # Process the recorded file
                        if self.recording_file and os.path.exists(self.recording_file):
                            logger.info(f'Processing {self.recording_file}...')
                            clips_dir = os.path.join(self.output_dir, 'clips')
                            clips = self.clipper.generate_clips(
                                self.recording_file,
                                clips_dir
                            )
                            logger.info(f'Generated {len(clips)} clips')
                        
                        self.recording_file = None
                    else:
                        logger.info('Waiting for stream to go live...')
                
                # Check every 30 seconds
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info('Shutting down...')
            if is_recording:
                self.monitor.stop_recording()
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            if is_recording:
                self.monitor.stop_recording()

def main():
    if not STREAMER_URL:
        logger.error('STREAMER_URL not configured. Please set it in .env file')
        return
    
    clipper = StreamClipper(STREAMER_URL, OUTPUT_DIR)
    clipper.run()

if __name__ == '__main__':
    main()
