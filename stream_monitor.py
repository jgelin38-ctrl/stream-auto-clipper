import subprocess
import logging
from datetime import datetime
import os
from config import STREAMER_URL, OUTPUT_DIR, LOG_DIR, QUALITY, FFMPEG_PATH

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'stream_monitor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StreamMonitor:
    """Monitor and capture live stream"""
    
    def __init__(self, streamer_url, output_dir, quality='best'):
        self.streamer_url = streamer_url
        self.output_dir = output_dir
        self.quality = quality
        self.process = None
        os.makedirs(output_dir, exist_ok=True)
        
    def start_recording(self):
        """Start recording the live stream"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f'stream_{timestamp}.mp4')
        
        try:
            logger.info(f'Starting stream recording from: {self.streamer_url}')
            
            # Use streamlink to pipe stream to ffmpeg
            streamlink_cmd = [
                'streamlink',
                '--stdout',
                self.streamer_url,
                self.quality
            ]
            
            ffmpeg_cmd = [
                FFMPEG_PATH,
                '-i', 'pipe:0',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '128k',
                output_file
            ]
            
            # Start streamlink process
            streamlink_process = subprocess.Popen(
                streamlink_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Pipe streamlink output to ffmpeg
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=streamlink_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            streamlink_process.stdout.close()  # Close streamlink stdout
            logger.info(f'Recording started, output: {output_file}')
            return output_file
            
        except Exception as e:
            logger.error(f'Error starting recording: {e}')
            return None
    
    def stop_recording(self):
        """Stop the current recording"""
        if self.process:
            try:
                logger.info('Stopping stream recording')
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info('Recording stopped successfully')
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning('Recording process killed')
            except Exception as e:
                logger.error(f'Error stopping recording: {e}')
    
    def is_streaming(self):
        """Check if stream is currently live"""
        try:
            result = subprocess.run(
                ['streamlink', '--json-output', self.streamer_url],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f'Error checking stream status: {e}')
            return False
