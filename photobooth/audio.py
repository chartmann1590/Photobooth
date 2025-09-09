"""
Audio and Text-to-Speech functionality using eSpeak
"""
import os
import logging
import subprocess
import threading
from typing import Optional, Dict, Any, List

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("pyttsx3 not available - falling back to eSpeak")

from .models import get_setting

logger = logging.getLogger(__name__)

def check_espeak_available() -> bool:
    """Check if eSpeak is available on the system"""
    try:
        result = subprocess.run(['espeak', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def get_espeak_voices() -> List[Dict[str, str]]:
    """Get available eSpeak voices"""
    try:
        result = subprocess.run(['espeak', '--voices'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return []
        
        voices = []
        lines = result.stdout.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 4:
                voices.append({
                    'code': parts[1],
                    'language': parts[2],
                    'name': ' '.join(parts[3:]) if len(parts) > 3 else parts[2]
                })
        
        return voices
        
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.error(f"Failed to get eSpeak voices: {e}")
        return []

def speak_text_espeak(text: str, voice: str = None, rate: int = None, 
                     async_mode: bool = True) -> bool:
    """Speak text using eSpeak"""
    try:
        if not check_espeak_available():
            logger.warning("eSpeak not available")
            return False
        
        # Get settings
        if voice is None:
            voice = get_setting('tts_voice', 'en+f3')
        if rate is None:
            rate = get_setting('tts_rate', 150)
        
        # Build command
        cmd = ['espeak', '-v', voice, '-s', str(rate), text]
        
        if async_mode:
            # Run in background thread
            def run_espeak():
                try:
                    subprocess.run(cmd, timeout=30, capture_output=True)
                except subprocess.TimeoutExpired:
                    logger.warning("eSpeak command timed out")
                except Exception as e:
                    logger.error(f"eSpeak error: {e}")
            
            thread = threading.Thread(target=run_espeak)
            thread.daemon = True
            thread.start()
        else:
            # Run synchronously
            result = subprocess.run(cmd, timeout=30, capture_output=True)
            if result.returncode != 0:
                logger.error(f"eSpeak failed with code {result.returncode}")
                return False
        
        logger.info(f"Speaking text: '{text[:50]}...' with voice {voice}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to speak text with eSpeak: {e}")
        return False

def speak_text_pyttsx3(text: str, voice: str = None, rate: int = None,
                      async_mode: bool = True) -> bool:
    """Speak text using pyttsx3"""
    try:
        if not TTS_AVAILABLE:
            return False
        
        # Get settings
        if rate is None:
            rate = get_setting('tts_rate', 150)
        
        def run_tts():
            try:
                engine = pyttsx3.init('espeak')
                
                # Set rate
                engine.setProperty('rate', rate)
                
                # Set voice if specified
                if voice:
                    voices = engine.getProperty('voices')
                    for v in voices:
                        if voice in v.id:
                            engine.setProperty('voice', v.id)
                            break
                
                # Speak text
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                
            except Exception as e:
                logger.error(f"pyttsx3 error: {e}")
        
        if async_mode:
            thread = threading.Thread(target=run_tts)
            thread.daemon = True
            thread.start()
        else:
            run_tts()
        
        logger.info(f"Speaking text with pyttsx3: '{text[:50]}...'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to speak text with pyttsx3: {e}")
        return False

def speak_text(text: str, voice: str = None, rate: int = None, 
               async_mode: bool = True) -> bool:
    """Speak text using available TTS engine"""
    try:
        # Check if TTS is enabled
        if not get_setting('tts_enabled', True):
            logger.info("TTS disabled in settings")
            return True  # Not an error, just disabled
        
        # Try pyttsx3 first, fall back to eSpeak
        if TTS_AVAILABLE:
            success = speak_text_pyttsx3(text, voice, rate, async_mode)
            if success:
                return True
        
        # Fall back to direct eSpeak
        return speak_text_espeak(text, voice, rate, async_mode)
        
    except Exception as e:
        logger.error(f"Failed to speak text: {e}")
        return False

def speak_countdown(countdown_text: str = None) -> bool:
    """Speak countdown with appropriate timing"""
    try:
        if countdown_text is None:
            countdown_text = "3, 2, 1, smile!"
        
        # Check if countdown is enabled
        if not get_setting('countdown_enabled', True):
            return True
        
        return speak_text(countdown_text, async_mode=True)
        
    except Exception as e:
        logger.error(f"Failed to speak countdown: {e}")
        return False

def play_sound_file(sound_path: str, async_mode: bool = True) -> bool:
    """Play a sound file using available audio tools"""
    try:
        if not os.path.exists(sound_path):
            logger.warning(f"Sound file not found: {sound_path}")
            return False
        
        # Try different audio players
        players = ['aplay', 'paplay', 'play', 'ffplay']
        
        for player in players:
            try:
                # Check if player is available
                result = subprocess.run(['which', player], 
                                      capture_output=True, timeout=5)
                if result.returncode != 0:
                    continue
                
                # Build command
                if player == 'ffplay':
                    cmd = [player, '-nodisp', '-autoexit', sound_path]
                elif player in ['aplay', 'paplay']:
                    cmd = [player, sound_path]
                elif player == 'play':
                    cmd = [player, sound_path, 'trim', '0', '5']  # Limit to 5 seconds
                else:
                    cmd = [player, sound_path]
                
                if async_mode:
                    # Run in background
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(cmd, timeout=10, capture_output=True)
                
                logger.info(f"Playing sound with {player}: {sound_path}")
                return True
                
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        logger.warning("No audio player found")
        return False
        
    except Exception as e:
        logger.error(f"Failed to play sound file: {e}")
        return False

def get_available_voices() -> List[Dict[str, str]]:
    """Get list of available voices from all sources"""
    voices = []
    
    # Get eSpeak voices
    espeak_voices = get_espeak_voices()
    for voice in espeak_voices:
        voices.append({
            'id': voice['code'],
            'name': f"{voice['name']} (eSpeak)",
            'language': voice['language'],
            'engine': 'espeak'
        })
    
    # Get pyttsx3 voices if available
    if TTS_AVAILABLE:
        try:
            engine = pyttsx3.init('espeak')
            pyttsx3_voices = engine.getProperty('voices')
            
            for voice in pyttsx3_voices or []:
                voices.append({
                    'id': voice.id,
                    'name': f"{voice.name} (pyttsx3)",
                    'language': getattr(voice, 'languages', ['unknown'])[0],
                    'engine': 'pyttsx3'
                })
            
            engine.stop()
            
        except Exception as e:
            logger.warning(f"Failed to get pyttsx3 voices: {e}")
    
    return voices

def test_tts(text: str = "PhotoBooth text to speech test") -> Dict[str, Any]:
    """Test TTS functionality"""
    results = {
        'espeak_available': check_espeak_available(),
        'pyttsx3_available': TTS_AVAILABLE,
        'voices_available': 0,
        'test_successful': False
    }
    
    # Count available voices
    voices = get_available_voices()
    results['voices_available'] = len(voices)
    
    # Test speaking
    try:
        success = speak_text(text, async_mode=False)
        results['test_successful'] = success
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def create_audio_notifications():
    """Create default audio notification files"""
    try:
        sounds_dir = os.path.join(os.path.dirname(__file__), 'static', 'sounds')
        os.makedirs(sounds_dir, exist_ok=True)
        
        # Create simple notification sounds using eSpeak if available
        if check_espeak_available():
            notifications = {
                'ready.wav': 'Ready',
                'countdown.wav': '3, 2, 1',
                'photo_taken.wav': 'Photo taken',
                'print_started.wav': 'Printing',
                'success.wav': 'Success'
            }
            
            for filename, text in notifications.items():
                sound_path = os.path.join(sounds_dir, filename)
                if not os.path.exists(sound_path):
                    try:
                        # Generate WAV file with eSpeak
                        cmd = ['espeak', '-w', sound_path, text]
                        result = subprocess.run(cmd, timeout=10, capture_output=True)
                        
                        if result.returncode == 0:
                            logger.info(f"Created notification sound: {filename}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to create {filename}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create audio notifications: {e}")
        return False

def validate_audio_settings() -> Dict[str, Any]:
    """Validate current audio configuration"""
    issues = []
    
    # Check if any TTS engine is available
    if not TTS_AVAILABLE and not check_espeak_available():
        issues.append("No TTS engine available (pyttsx3 or eSpeak)")
    
    # Check voice setting
    current_voice = get_setting('tts_voice', 'en+f3')
    available_voices = get_available_voices()
    voice_found = any(v['id'] == current_voice for v in available_voices)
    
    if not voice_found and available_voices:
        issues.append(f"Configured voice '{current_voice}' not found")
    
    # Check rate setting
    rate = get_setting('tts_rate', 150)
    if not isinstance(rate, int) or rate < 50 or rate > 300:
        issues.append(f"Invalid TTS rate: {rate} (should be 50-300)")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'tts_enabled': get_setting('tts_enabled', True),
        'available_engines': {
            'espeak': check_espeak_available(),
            'pyttsx3': TTS_AVAILABLE
        },
        'voices_count': len(available_voices)
    }