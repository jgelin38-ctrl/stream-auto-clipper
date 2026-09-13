import subprocess
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path
from config import CLIP_DURATION, FFMPEG_PATH, LOG_DIR

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'clip_generator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClipGenerator:
    """Generate clips from recorded streams"""
    
    def __init__(self, clip_duration=80):
        self.clip_duration = clip_duration
    
    def get_video_duration(self, video_path):
        """Get the duration of a video file in seconds"""
        try:
            result = subprocess.run(
                [
                    FFMPEG_PATH,
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1:nokey=1',
                    video_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f'Error getting video duration: {e}')
            return 0
    
    def generate_clips(self, input_video, output_dir, clip_duration=None):
        """Generate 80-second clips from input video"""
        if clip_duration is None:
            clip_duration = self.clip_duration
        
        try:
            duration = self.get_video_duration(input_video)
            if duration == 0:
                logger.error(f'Could not determine duration of {input_video}')
                return []
            
            logger.info(f'Video duration: {duration:.2f} seconds')
            os.makedirs(output_dir, exist_ok=True)
            
            clips = []
            clip_count = 0
            start_time = 0
            
            while start_time < duration:
                clip_count += 1
                end_time = min(start_time + clip_duration, duration)
                clip_duration_actual = end_time - start_time
                
                # Generate timestamp-based filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(
                    output_dir,
                    f'clip_{timestamp}_part{clip_count:02d}.mp4'
                )
                
                logger.info(
                    f'Generating clip {clip_count}: '
                    f'{start_time:.2f}s - {end_time:.2f}s '
                    f'(Duration: {clip_duration_actual:.2f}s)'
                )
                
                cmd = [
                    FFMPEG_PATH,
                    '-i', input_video,
                    '-ss', str(start_time),
                    '-to', str(end_time),
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-y',
                    output_file
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    clips.append(output_file)
                    logger.info(f'Clip created successfully: {output_file}')
                else:
                    logger.error(f'Failed to create clip {clip_count}')
                
                start_time = end_time
            
            logger.info(f'Generated {len(clips)} clips from {input_video}')
            return clips
            
        except Exception as e:
            logger.error(f'Error generating clips: {e}')
            return []
