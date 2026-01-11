"""Tests for voice input module."""

import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import httpx

from smarthome_mock_ai.voice import VoiceListener, get_default_voice_listener


@pytest.fixture
def voice_listener():
    """Create a VoiceListener instance for testing."""
    return VoiceListener(timeout=5, phrase_threshold=0.5)


class TestVoiceListenerInit:
    """Test VoiceListener initialization."""

    def test_init_without_speech_recognition(self):
        """Test initialization when speech_recognition is not available."""
        # Mock the import to raise ImportError
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "speech_recognition":
                raise ImportError("No module named 'speech_recognition'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            listener = VoiceListener()
            assert listener.sr is None
            assert listener.timeout == 5
            assert listener.phrase_threshold == 0.5

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        listener = VoiceListener(timeout=10, phrase_threshold=1.0)
        assert listener.timeout == 10
        assert listener.phrase_threshold == 1.0


class TestVoiceListenerIsAvailable:
    """Test VoiceListener.is_available method."""

    def test_is_available_when_sr_is_none(self, voice_listener):
        """Test is_available returns False when speech_recognition is not available."""
        voice_listener.sr = None
        assert voice_listener.is_available() is False

    def test_is_available_when_no_microphones(self, voice_listener):
        """Test is_available returns False when no microphones are found."""
        mock_sr = MagicMock()
        mock_sr.Microphone.list_microphone_names.return_value = []
        voice_listener.sr = mock_sr
        assert voice_listener.is_available() is False

    def test_is_available_when_microphone_found(self, voice_listener):
        """Test is_available returns True when microphone is available."""
        mock_sr = MagicMock()
        mock_sr.Microphone.list_microphone_names.return_value = ["Test Mic"]
        voice_listener.sr = mock_sr
        assert voice_listener.is_available() is True

    def test_is_available_on_os_error(self, voice_listener):
        """Test is_available returns False on OSError."""
        mock_sr = MagicMock()
        mock_sr.Microphone.list_microphone_names.side_effect = OSError("No mic")
        voice_listener.sr = mock_sr
        assert voice_listener.is_available() is False


class TestVoiceListenerListMicrophones:
    """Test VoiceListener.list_microphones method."""

    def test_list_microphones_when_sr_is_none(self, voice_listener):
        """Test list_microphones returns empty list when sr is None."""
        voice_listener.sr = None
        result = voice_listener.list_microphones()
        assert result == []

    def test_list_microphones_success(self, voice_listener):
        """Test list_microphones returns correct list."""
        mock_sr = MagicMock()
        mock_sr.Microphone.list_microphone_names.return_value = ["Mic 1", "Mic 2"]
        voice_listener.sr = mock_sr
        result = voice_listener.list_microphones()
        assert result == [(0, "Mic 1"), (1, "Mic 2")]


class TestVoiceListenerTranscribe:
    """Test VoiceListener.transcribe method."""

    @pytest.mark.asyncio
    async def test_transcribe_without_api_key(self, voice_listener, tmp_path):
        """Test transcribe raises error when API key is not set."""
        # Ensure OPENAI_API_KEY is not set
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            # Create new listener to pick up the env change
            listener = VoiceListener()
            test_file = tmp_path / "test.wav"
            test_file.write_text("dummy")

            with pytest.raises(RuntimeError, match="OPENAI_API_KEY not set"):
                await listener.transcribe(str(test_file))

    @pytest.mark.asyncio
    async def test_transcribe_with_file_not_found(self, voice_listener):
        """Test transcribe raises error when file not found."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            listener = VoiceListener()

            with pytest.raises(RuntimeError, match="Audio file not found"):
                await listener.transcribe("/nonexistent/file.wav")

    @pytest.mark.asyncio
    async def test_transcribe_api_success(self, voice_listener, tmp_path):
        """Test transcribe with successful API response."""
        # Create a minimal WAV file
        import wave
        import struct

        wav_path = tmp_path / "test.wav"
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # Write a small amount of data
            wav_file.writeframes(struct.pack("<h", 0))

        mock_response = MagicMock()
        mock_response.json.return_value = {"text": "打开客厅灯"}
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            listener = VoiceListener()
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
                result = await listener.transcribe(str(wav_path))

                assert result == "打开客厅灯"
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"
                assert "files" in call_args[1]
                assert "data" in call_args[1]

    @pytest.mark.asyncio
    async def test_transcribe_api_http_error(self, voice_listener, tmp_path):
        """Test transcribe handles HTTP errors properly."""
        import wave
        import struct

        wav_path = tmp_path / "test.wav"
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(struct.pack("<h", 0))

        mock_error_response = MagicMock()
        mock_error_response.text = "Unauthorized"
        mock_error_response.status_code = 401

        http_error = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_error_response
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            listener = VoiceListener()
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=http_error):
                with pytest.raises(RuntimeError, match="Transcription API error"):
                    await listener.transcribe(str(wav_path))


class TestVoiceListenerListen:
    """Test VoiceListener.listen method."""

    def test_listen_when_not_available(self, voice_listener):
        """Test listen raises error when microphone is not available."""
        voice_listener.sr = None
        with pytest.raises(RuntimeError, match="Microphone not available"):
            voice_listener.listen()

    def test_listen_timeout_error(self, voice_listener):
        """Test listen handles timeout errors properly."""
        mock_sr = MagicMock()
        mock_sr.Microphone.list_microphone_names.return_value = ["Test Mic"]
        mock_sr.WaitTimeoutError = Exception
        voice_listener.sr = mock_sr

        mock_recognizer = MagicMock()
        mock_recognizer.listen.side_effect = Exception("No speech")
        mock_sr.Recognizer.return_value = mock_recognizer

        mock_mic_instance = MagicMock()
        mock_mic_instance.__enter__ = Mock(return_value=mock_mic_instance)
        mock_mic_instance.__exit__ = Mock(return_value=False)
        mock_sr.Microphone.return_value = mock_mic_instance

        # This should raise RuntimeError with timeout message
        with pytest.raises(RuntimeError):
            voice_listener.listen()


class TestGetDefaultVoiceListener:
    """Test get_default_voice_listener function."""

    def test_returns_voice_listener_instance(self):
        """Test that get_default_voice_listener returns VoiceListener instance."""
        listener = get_default_voice_listener()
        assert isinstance(listener, VoiceListener)
        assert listener.timeout == 5
        assert listener.phrase_threshold == 10


class TestVoiceListenerOpenAIKeyProperty:
    """Test VoiceListener.OPENAI_API_KEY property."""

    def test_returns_env_variable(self):
        """Test that OPENAI_API_KEY returns environment variable value."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"}):
            listener = VoiceListener()
            assert listener.OPENAI_API_KEY == "test-key-123"

    def test_returns_empty_string_when_not_set(self):
        """Test that OPENAI_API_KEY returns empty string when not set."""
        with patch.dict(os.environ, {}, clear=True):
            listener = VoiceListener()
            assert listener.OPENAI_API_KEY == ""
