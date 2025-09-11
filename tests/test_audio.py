"""
Tests for audio functionality (mocked since TTS may not be available)
"""
import pytest
from unittest.mock import patch, MagicMock

from photobooth.audio import (
    check_espeak_available, speak_text_espeak, speak_text_pyttsx3,
    speak_text, speak_countdown, get_available_voices, test_tts,
    validate_audio_settings
)

@patch('subprocess.run')
def test_check_espeak_available_true(mock_run):
    """Test eSpeak availability check - available"""
    mock_run.return_value.returncode = 0
    assert check_espeak_available() is True

@patch('subprocess.run')
def test_check_espeak_available_false(mock_run):
    """Test eSpeak availability check - not available"""
    mock_run.side_effect = FileNotFoundError()
    assert check_espeak_available() is False

@patch('photobooth.audio.check_espeak_available')
@patch('photobooth.audio.get_setting')
@patch('subprocess.run')
@patch('threading.Thread')
def test_speak_text_espeak_async(mock_thread, mock_run, mock_get_setting, mock_check):
    """Test eSpeak text-to-speech in async mode"""
    mock_check.return_value = True
    mock_get_setting.side_effect = lambda key, default: {'tts_voice': 'en+f3', 'tts_rate': 150}.get(key, default)
    
    result = speak_text_espeak('Hello world', async_mode=True)
    
    assert result is True
    mock_thread.assert_called_once()

@patch('photobooth.audio.check_espeak_available')
@patch('photobooth.audio.get_setting')
@patch('subprocess.run')
def test_speak_text_espeak_sync(mock_run, mock_get_setting, mock_check):
    """Test eSpeak text-to-speech in sync mode"""
    mock_check.return_value = True
    mock_get_setting.side_effect = lambda key, default: {'tts_voice': 'en+f3', 'tts_rate': 150}.get(key, default)
    mock_run.return_value.returncode = 0
    
    result = speak_text_espeak('Hello world', async_mode=False)
    
    assert result is True
    mock_run.assert_called_once()

@patch('photobooth.audio.TTS_AVAILABLE', True)
@patch('pyttsx3.init')
@patch('threading.Thread')
def test_speak_text_pyttsx3_async(mock_thread, mock_init):
    """Test pyttsx3 text-to-speech in async mode"""
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine
    
    result = speak_text_pyttsx3('Hello world', async_mode=True)
    
    assert result is True
    mock_thread.assert_called_once()

@patch('photobooth.audio.get_setting')
@patch('photobooth.audio.TTS_AVAILABLE', True)
@patch('photobooth.audio.speak_text_pyttsx3')
def test_speak_text_prefers_pyttsx3(mock_pyttsx3, mock_get_setting):
    """Test that speak_text prefers pyttsx3 when available"""
    mock_get_setting.return_value = True  # TTS enabled
    mock_pyttsx3.return_value = True
    
    result = speak_text('Hello world')
    
    assert result is True
    mock_pyttsx3.assert_called_once()

@patch('photobooth.audio.get_setting')
@patch('photobooth.audio.TTS_AVAILABLE', False)
@patch('photobooth.audio.speak_text_espeak')
def test_speak_text_fallback_espeak(mock_espeak, mock_get_setting):
    """Test that speak_text falls back to eSpeak"""
    mock_get_setting.return_value = True  # TTS enabled
    mock_espeak.return_value = True
    
    result = speak_text('Hello world')
    
    assert result is True
    mock_espeak.assert_called_once()

@patch('photobooth.audio.get_setting')
def test_speak_text_disabled(mock_get_setting):
    """Test speak_text when TTS is disabled"""
    mock_get_setting.return_value = False  # TTS disabled
    
    result = speak_text('Hello world')
    
    assert result is True  # Should succeed but do nothing

@patch('photobooth.audio.get_setting')
@patch('photobooth.audio.speak_text')
def test_speak_countdown_enabled(mock_speak, mock_get_setting):
    """Test countdown speech when enabled"""
    mock_get_setting.return_value = True  # Countdown enabled
    mock_speak.return_value = True
    
    result = speak_countdown()
    
    assert result is True
    mock_speak.assert_called_once_with('3, 2, 1, smile!', async_mode=True)

@patch('photobooth.audio.get_setting')
def test_speak_countdown_disabled(mock_get_setting):
    """Test countdown speech when disabled"""
    mock_get_setting.return_value = False  # Countdown disabled
    
    result = speak_countdown()
    
    assert result is True  # Should succeed but do nothing

@patch('subprocess.run')
def test_get_espeak_voices(mock_run):
    """Test getting eSpeak voices"""
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = """Pty Language Age/Gender VoiceName          File          Other Languages
 5  af             M  afrikaans            other/af
 5  am             M  amharic              other/am
 5  an             M  aragonese            other/an
 5  ar             M  arabic               other/ar
 5  as             M  assamese             other/as
 5  az             M  azerbaijani          other/az
 5  bg             M  bulgarian            other/bg"""
    
    voices = get_espeak_voices()
    
    assert len(voices) > 0
    assert voices[0]['code'] == 'af'
    assert voices[0]['language'] == 'afrikaans'

@patch('photobooth.audio.get_espeak_voices')
@patch('photobooth.audio.TTS_AVAILABLE', True)
@patch('pyttsx3.init')
def test_get_available_voices(mock_init, mock_espeak_voices):
    """Test getting all available voices"""
    mock_espeak_voices.return_value = [
        {'code': 'en+f3', 'language': 'english', 'name': 'English Female'}
    ]
    
    mock_engine = MagicMock()
    mock_voice = MagicMock()
    mock_voice.id = 'english+f3'
    mock_voice.name = 'English Female'
    mock_voice.languages = ['en']
    mock_engine.getProperty.return_value = [mock_voice]
    mock_init.return_value = mock_engine
    
    voices = get_available_voices()
    
    assert len(voices) >= 1
    # Should have both eSpeak and pyttsx3 voices
    espeak_voices = [v for v in voices if v['engine'] == 'espeak']
    pyttsx3_voices = [v for v in voices if v['engine'] == 'pyttsx3']
    assert len(espeak_voices) > 0
    assert len(pyttsx3_voices) > 0

@patch('photobooth.audio.check_espeak_available')
@patch('photobooth.audio.TTS_AVAILABLE', True)
@patch('photobooth.audio.speak_text')
def test_test_tts_success(mock_speak, mock_check):
    """Test TTS functionality test - success"""
    mock_check.return_value = True
    mock_speak.return_value = True
    
    result = test_tts()
    
    assert result['espeak_available'] is True
    assert result['pyttsx3_available'] is True
    assert result['test_successful'] is True

@patch('photobooth.audio.check_espeak_available')
@patch('photobooth.audio.TTS_AVAILABLE', False)
@patch('photobooth.audio.get_setting')
def test_validate_audio_settings_no_tts(mock_get_setting, mock_check):
    """Test audio settings validation with no TTS available"""
    mock_check.return_value = False
    mock_get_setting.side_effect = lambda key, default: {
        'tts_voice': 'en+f3',
        'tts_rate': 150
    }.get(key, default)
    
    result = validate_audio_settings()
    
    assert result['valid'] is False
    assert any('No TTS engine' in issue for issue in result['issues'])

@patch('photobooth.audio.check_espeak_available')
@patch('photobooth.audio.TTS_AVAILABLE', True)
@patch('photobooth.audio.get_setting')
@patch('photobooth.audio.get_available_voices')
def test_validate_audio_settings_invalid_rate(mock_voices, mock_get_setting, mock_check):
    """Test audio settings validation with invalid rate"""
    mock_check.return_value = True
    mock_get_setting.side_effect = lambda key, default: {
        'tts_voice': 'en+f3',
        'tts_rate': 500  # Too high
    }.get(key, default)
    mock_voices.return_value = [{'id': 'en+f3'}]
    
    result = validate_audio_settings()
    
    assert result['valid'] is False
    assert any('Invalid TTS rate' in issue for issue in result['issues'])