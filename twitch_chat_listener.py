import socket
import re
import logging
import threading
from datetime import datetime
import os
from config import LOG_DIR
from chat_detector import ChatDetector

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'twitch_chat.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitchChatListener:
    """Listens to Twitch chat and detects interaction spikes"""
    
    def __init__(self, channel_name):
        self.channel_name = channel_name.lower()
        self.host = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nick = 'justinfan' + ''.join([str(i) for i in range(10)])  # Anonymous connection
        self.chat_detector = ChatDetector(channel_name)
        self.socket = None
        self.connected = False
        self.running = False
        
    def connect(self):
        """Connect to Twitch IRC chat"""
        try:
            logger.info(f'Connecting to Twitch chat for channel: {self.channel_name}')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Send connection commands
            self.socket.send(f'NICK {self.nick}\r\n'.encode())
            self.socket.send(f'JOIN #{self.channel_name}\r\n'.encode())
            
            self.connected = True
            logger.info(f'Connected to #{self.channel_name}')
            
        except Exception as e:
            logger.error(f'Failed to connect to Twitch chat: {e}')
            self.connected = False
    
    def disconnect(self):
        """Disconnect from Twitch IRC"""
        if self.socket:
            try:
                self.socket.close()
                self.connected = False
                logger.info(f'Disconnected from #{self.channel_name}')
            except Exception as e:
                logger.error(f'Error disconnecting: {e}')
    
    def start_listening(self):
        """Start listening to chat messages in a separate thread"""
        self.running = True
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()
        return thread
    
    def stop_listening(self):
        """Stop listening to chat"""
        self.running = False
        self.disconnect()
    
    def _listen_loop(self):
        """Main loop for listening to chat"""
        self.connect()
        
        if not self.connected:
            return
        
        try:
            while self.running and self.connected:
                try:
                    message = self.socket.recv(2048).decode('utf-8')
                    
                    if not message:
                        logger.warning('Connection lost, reconnecting...')
                        self.disconnect()
                        self.connect()
                        continue
                    
                    # Process PING/PONG to keep connection alive
                    if message.startswith('PING'):
                        self.socket.send('PONG\r\n'.encode())
                        continue
                    
                    # Parse chat message
                    self._process_message(message)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f'Error receiving message: {e}')
                    self.disconnect()
                    self.connect()
                    
        except Exception as e:
            logger.error(f'Listen loop error: {e}')
        finally:
            self.disconnect()
    
    def _process_message(self, raw_message):
        """Process IRC message and detect chat spikes"""
        try:
            # Parse IRC message format
            # Example: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message text
            
            lines = raw_message.split('\r\n')
            
            for line in lines:
                if not line or 'PRIVMSG' not in line:
                    continue
                
                # Extract username and message
                match = re.search(r':([\w]+)!\1@\1\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)', line)
                
                if match:
                    username = match.group(1)
                    message_text = match.group(2)
                    timestamp = datetime.now()
                    
                    # Add message to detector
                    spike = self.chat_detector.add_message(message_text, timestamp)
                    
                    if spike:
                        logger.info(
                            f'[{self.channel_name}] Spike detected! '
                            f'Type: {spike.spike_type}, '
                            f'Messages: {spike.message_count}'
                        )
                        
        except Exception as e:
            logger.debug(f'Error processing message: {e}')
    
    def get_detector(self):
        """Get the chat detector instance"""
        return self.chat_detector
    
    def get_stats(self):
        """Get chat listener statistics"""
        return {
            'channel': self.channel_name,
            'connected': self.connected,
            'running': self.running,
            **self.chat_detector.get_stats()
        }
