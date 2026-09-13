# Stream Auto-Clipper

Automatically clip live streams into 80-second clips using Python.

## Features

- 🎬 Automatic stream detection and recording
- ✂️ Automatic 80-second clip generation
- 📝 Detailed logging
- 🎯 Support for multiple streaming platforms (Twitch, YouTube, etc.)
- ⚙️ Customizable configuration

## Requirements

- Python 3.7+
- FFmpeg (must be installed on your system)
- Streamlink

## Installation

### 1. Install System Dependencies

**On Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**On macOS (with Homebrew):**
```bash
brew install ffmpeg
```

**On Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use:
```bash
choco install ffmpeg
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and set your streamer URL:
```env
STREAMER_URL=https://www.twitch.tv/your_streamer_name
OUTPUT_DIR=./clips
QUALITY=best
```

## Usage

### Basic Usage

```bash
python main.py
```

The script will:
1. Check if the streamer is live
2. Start recording when stream goes live
3. Stop recording when stream ends
4. Automatically generate 80-second clips from the recording

### Supported Platforms

- Twitch
- YouTube
- Dailymotion
- And any platform supported by Streamlink

## Project Structure

```
stream-auto-clipper/
├── main.py              # Main entry point
├── config.py            # Configuration settings
├── stream_monitor.py    # Stream monitoring and recording
├── clip_generator.py    # Clip generation logic
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `STREAMER_URL` | URL of the streamer to monitor | Required |
| `CLIP_DURATION` | Length of each clip in seconds | 80 |
| `OUTPUT_DIR` | Directory to save clips | ./clips |
| `LOG_DIR` | Directory for log files | ./logs |
| `QUALITY` | Stream quality | best |
| `FFMPEG_PATH` | Path to FFmpeg executable | ffmpeg |

## Logs

Logs are saved in the `./logs/` directory:
- `main.log` - Main application log
- `stream_monitor.log` - Stream monitoring logs
- `clip_generator.log` - Clip generation logs

## Troubleshooting

### FFmpeg not found
```bash
# Update FFMPEG_PATH in .env if installed elsewhere
FFMPEG_PATH=/usr/local/bin/ffmpeg
```

### Stream not detected
- Verify the streamer URL is correct
- Check if the streamer is currently live
- Verify your internet connection

### Clips not being generated
- Check the logs in `./logs/` directory
- Verify FFmpeg is installed correctly
- Ensure sufficient disk space

## Performance Tips

1. **Reduce clip size**: Lower the quality setting if needed
   ```env
   QUALITY=720p60
   ```

2. **Faster encoding**: Use `ultrafast` preset (lower quality)
   - Modify `preset` in `clip_generator.py`

3. **Storage**: Keep clips on an SSD for faster processing

## Advanced Usage

### Custom Clip Duration

Edit `config.py`:
```python
CLIP_DURATION = 120  # 2 minutes instead of 80 seconds
```

### Disable Automatic Clip Generation

Comment out the clip generation in `main.py` to just record streams without clipping.

## License

MIT License - Feel free to use and modify

## Support

For issues or questions, please create an issue on the repository.
