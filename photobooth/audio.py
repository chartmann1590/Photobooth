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
        # Try espeak-ng first, then espeak
        for cmd in ['espeak-ng', 'espeak']:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            except FileNotFoundError:
                continue
        return False
    except (subprocess.TimeoutExpired, Exception):
        return False

def get_espeak_voices() -> List[Dict[str, str]]:
    """Get available eSpeak voices"""
    try:
        # Try espeak-ng first, then espeak
        for cmd in ['espeak-ng', 'espeak']:
            try:
                result = subprocess.run([cmd, '--voices'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    break
            except FileNotFoundError:
                continue
        else:
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

def get_enhanced_voice_options() -> List[Dict[str, str]]:
    """Get enhanced voice options with more natural sounding descriptions"""
    enhanced_voices = [
        # Female voices with improved descriptions
        {'id': 'en+f3', 'name': 'Sarah - Cheerful Female', 'language': 'English', 'description': 'Bright and welcoming female voice'},
        {'id': 'en+f5', 'name': 'Emma - Gentle Female', 'language': 'English', 'description': 'Soft and friendly female voice'},
        {'id': 'en+f2', 'name': 'Grace - Professional Female', 'language': 'English', 'description': 'Clear and professional female voice'},
        {'id': 'en+f1', 'name': 'Luna - Warm Female', 'language': 'English', 'description': 'Warm and inviting female voice'},
        {'id': 'en+f4', 'name': 'Aria - Whisper Female', 'language': 'English', 'description': 'Soft whisper female voice'},
        
        # Male voices with improved descriptions
        {'id': 'en+m3', 'name': 'David - Confident Male', 'language': 'English', 'description': 'Strong and confident male voice'},
        {'id': 'en+m5', 'name': 'Oliver - Friendly Male', 'language': 'English', 'description': 'Warm and approachable male voice'},
        {'id': 'en+m2', 'name': 'James - Professional Male', 'language': 'English', 'description': 'Clear and authoritative male voice'},
        {'id': 'en+m1', 'name': 'Alex - Gentle Male', 'language': 'English', 'description': 'Calm and reassuring male voice'},
        {'id': 'en+m4', 'name': 'Ryan - Whisper Male', 'language': 'English', 'description': 'Soft whisper male voice'},
        
        # Alternative accents and variants
        {'id': 'en-gb+f3', 'name': 'Sophie - British Female', 'language': 'English (UK)', 'description': 'Elegant British female voice'},
        {'id': 'en-gb+m3', 'name': 'William - British Male', 'language': 'English (UK)', 'description': 'Distinguished British male voice'},
        {'id': 'en-us+f3', 'name': 'Madison - American Female', 'language': 'English (US)', 'description': 'Clear American female voice'},
        {'id': 'en-us+m3', 'name': 'Jake - American Male', 'language': 'English (US)', 'description': 'Friendly American male voice'},
        
        # Slower, more deliberate voices for weddings
        {'id': 'en+f3+s120', 'name': 'Bella - Elegant Female (Slow)', 'language': 'English', 'description': 'Graceful and unhurried female voice'},
        {'id': 'en+m3+s120', 'name': 'Marcus - Dignified Male (Slow)', 'language': 'English', 'description': 'Distinguished and measured male voice'},
    ]
    
    return enhanced_voices

def speak_text_espeak(text: str, voice: str = None, rate: int = None, 
                     async_mode: bool = True) -> bool:
    """Speak text using eSpeak"""
    try:
        if not check_espeak_available():
            logger.warning("eSpeak not available")
            return False
        
        # Get settings with fallbacks
        if voice is None:
            try:
                voice = get_setting('tts_voice', 'en+f3')
            except:
                voice = 'en+f3'  # Fallback if Flask context not available
        if rate is None:
            try:
                rate = get_setting('tts_rate', 150)
            except:
                rate = 150  # Fallback if Flask context not available
        
        # Parse custom voice parameters (e.g., "en+f3+s120" for speed)
        espeak_voice = voice
        custom_rate = rate
        if '+s' in voice:
            voice_parts = voice.split('+')
            espeak_voice = '+'.join(voice_parts[:-1]) if len(voice_parts) > 2 else voice_parts[0]
            try:
                custom_rate = int(voice_parts[-1].replace('s', ''))
            except:
                pass
        
        # Get the correct espeak command
        espeak_cmd = 'espeak-ng'
        for cmd_name in ['espeak-ng', 'espeak']:
            try:
                subprocess.run([cmd_name, '--version'], capture_output=True, timeout=2)
                espeak_cmd = cmd_name
                break
            except FileNotFoundError:
                continue
        
        # Build command with explicit ALSA output
        cmd = [espeak_cmd, '-v', espeak_voice, '-s', str(custom_rate), '--stdout', text]
        # Use aplay to force ALSA output with full path
        aplay_cmd = ['/usr/bin/aplay', '-D', 'default']
        
        if async_mode:
            # Run in background thread
            def run_espeak():
                try:
                    # Pipe eSpeak output to aplay for better audio control
                    espeak_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    aplay_proc = subprocess.Popen(aplay_cmd, stdin=espeak_proc.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    espeak_proc.stdout.close()  # Allow espeak_proc to receive SIGPIPE if aplay_proc exits
                    aplay_proc.wait(timeout=30)
                    espeak_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("eSpeak/aplay command timed out")
                except Exception as e:
                    logger.error(f"eSpeak/aplay error: {e}")
            
            thread = threading.Thread(target=run_espeak)
            thread.daemon = True
            thread.start()
        else:
            # Run synchronously
            try:
                espeak_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                aplay_proc = subprocess.Popen(aplay_cmd, stdin=espeak_proc.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                espeak_proc.stdout.close()
                aplay_proc.wait(timeout=30)
                espeak_proc.wait(timeout=5)
                if aplay_proc.returncode != 0:
                    logger.error(f"aplay failed with code {aplay_proc.returncode}")
                    return False
            except subprocess.TimeoutExpired:
                logger.error("eSpeak/aplay command timed out")
                return False
            except Exception as e:
                logger.error(f"eSpeak/aplay error: {e}")
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
        
        # Get settings with fallbacks
        if rate is None:
            try:
                rate = get_setting('tts_rate', 150)
            except:
                rate = 150  # Fallback if Flask context not available
        
        def run_tts():
            engine = None
            try:
                engine = pyttsx3.init('espeak', debug=False)
                
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
                
            except Exception as e:
                logger.error(f"pyttsx3 error: {e}")
            finally:
                if engine:
                    try:
                        engine.stop()
                        del engine
                    except:
                        pass
        
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
        try:
            tts_enabled = get_setting('tts_enabled', True)
        except:
            tts_enabled = True  # Fallback if Flask context not available
            
        if not tts_enabled:
            logger.info("TTS disabled in settings")
            return True  # Not an error, just disabled
        
        # Use direct eSpeak only - pyttsx3 has threading issues
        return speak_text_espeak(text, voice, rate, async_mode)
        
    except Exception as e:
        logger.error(f"Failed to speak text: {e}")
        return False

def speak_countdown(countdown_text: str = None) -> bool:
    """Speak countdown with appropriate timing"""
    try:
        if countdown_text is None:
            # Use custom countdown message if available
            try:
                custom_message = get_setting('countdown_message', '')
                if custom_message:
                    countdown_text = custom_message + " 3, 2, 1, smile!"
                else:
                    countdown_text = "3, 2, 1, smile!"
            except:
                countdown_text = "3, 2, 1, smile!"
        
        # Check if countdown is enabled
        if not get_setting('countdown_enabled', True):
            return True
        
        return speak_text(countdown_text, async_mode=True)
        
    except Exception as e:
        logger.error(f"Failed to speak countdown: {e}")
        return False

def speak_welcome() -> bool:
    """Speak welcome message"""
    try:
        welcome_message = get_setting('welcome_message', 'Welcome to our photobooth!')
        
        # Check if TTS is enabled
        if not get_setting('tts_enabled', True):
            return True
        
        return speak_text(welcome_message, async_mode=True)
        
    except Exception as e:
        logger.error(f"Failed to speak welcome: {e}")
        return False

def speak_photo_captured() -> bool:
    """Speak photo captured message"""
    try:
        capture_message = get_setting('capture_message', 'Perfect! Photo captured!')
        
        # Check if TTS is enabled
        if not get_setting('tts_enabled', True):
            return True
        
        return speak_text(capture_message, async_mode=True)
        
    except Exception as e:
        logger.error(f"Failed to speak photo captured: {e}")
        return False

def speak_print_success() -> bool:
    """Speak print success message"""
    try:
        print_message = get_setting('print_message', 'Your photo is printing!')
        
        # Check if TTS is enabled
        if not get_setting('tts_enabled', True):
            return True
        
        return speak_text(print_message, async_mode=True)
        
    except Exception as e:
        logger.error(f"Failed to speak print success: {e}")
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
    
    # Start with enhanced voice options (curated for better user experience)
    enhanced_voices = get_enhanced_voice_options()
    for voice in enhanced_voices:
        voices.append({
            'id': voice['id'],
            'name': voice['name'],
            'language': voice['language'],
            'description': voice.get('description', ''),
            'engine': 'espeak'
        })
    
    # Add system eSpeak voices (for completeness)
    espeak_voices = get_espeak_voices()
    for voice in espeak_voices:
        # Skip if already included in enhanced voices
        if not any(v['id'] == voice['code'] or voice['code'] in v['id'] for v in enhanced_voices):
            voices.append({
                'id': voice['code'],
                'name': f"{voice['name']} (System)",
                'language': voice['language'],
                'description': 'System voice',
                'engine': 'espeak'
            })
    
    # Get pyttsx3 voices if available (keeping for compatibility)
    if TTS_AVAILABLE:
        engine = None
        try:
            engine = pyttsx3.init('espeak', debug=False)
            pyttsx3_voices = engine.getProperty('voices')
            
            for voice in pyttsx3_voices or []:
                # Convert bytes to strings if needed
                voice_id = voice.id.decode('utf-8') if isinstance(voice.id, bytes) else voice.id
                voice_name = voice.name.decode('utf-8') if isinstance(voice.name, bytes) else voice.name
                languages = getattr(voice, 'languages', ['unknown'])
                if languages and isinstance(languages[0], bytes):
                    language = languages[0].decode('utf-8')
                else:
                    language = languages[0] if languages else 'unknown'
                
                # Skip if already included
                if not any(v['id'] == voice_id for v in voices):
                    voices.append({
                        'id': voice_id,
                        'name': f"{voice_name} (pyttsx3)",
                        'language': language,
                        'description': 'pyttsx3 voice',
                        'engine': 'pyttsx3'
                    })
            
        except Exception as e:
            logger.warning(f"Failed to get pyttsx3 voices: {e}")
        finally:
            if engine:
                try:
                    engine.stop()
                    del engine
                except:
                    pass
    
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

def get_tts_status() -> Dict[str, Any]:
    """Get current TTS engine status"""
    try:
        espeak_available = check_espeak_available()
        pyttsx3_available = TTS_AVAILABLE
        
        # Determine which engine is being used
        engine = "None"
        available = False
        
        if pyttsx3_available:
            engine = "pyttsx3 + eSpeak"
            available = True
        elif espeak_available:
            engine = "eSpeak (direct)"
            available = True
        
        return {
            'available': available,
            'engine': engine,
            'espeak': espeak_available,
            'pyttsx3': pyttsx3_available,
            'enabled': get_setting('tts_enabled', True)
        }
        
    except Exception as e:
        logger.error(f"Error getting TTS status: {e}")
        return {
            'available': False,
            'engine': 'Error',
            'error': str(e)
        }