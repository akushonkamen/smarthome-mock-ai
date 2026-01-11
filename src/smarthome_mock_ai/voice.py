"""Voice Input Module - Handles audio recording and transcription."""

import os
import tempfile
import wave
from typing import Any

import httpx


class VoiceListener:
    """Voice listener for recording and transcribing audio input."""

    # OpenAI Whisper API configuration
    WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

    @property
    def OPENAI_API_KEY(self) -> str:
        """Get OpenAI API Key for Whisper transcription."""
        return os.getenv("OPENAI_API_KEY", "")

    def __init__(self, timeout: int = 5, phrase_threshold: float = 0.5) -> None:
        """Initialize VoiceListener.

        Args:
            timeout: Maximum seconds to wait for speech to start
            phrase_threshold: Minimum seconds of silence to mark end of phrase
        """
        self.timeout = timeout
        self.phrase_threshold = phrase_threshold
        self.sr = None
        self._init_speech_recognition()

    def _init_speech_recognition(self) -> None:
        """Initialize speech recognition library.

        Gracefully handles cases where pyaudio is not available.
        """
        try:
            import speech_recognition as sr

            self.sr = sr
        except ImportError:
            self.sr = None

    def is_available(self) -> bool:
        """Check if voice input is available.

        Returns:
            True if speech recognition and microphone are available
        """
        if self.sr is None:
            return False

        try:
            recognizer = self.sr.Recognizer()
            # Try to list microphones
            mic_list = self.sr.Microphone.list_microphone_names()
            return len(mic_list) > 0
        except (OSError, AttributeError):
            return False

    def list_microphones(self) -> list[tuple[int, str]]:
        """List available microphones.

        Returns:
            List of (device_index, device_name) tuples
        """
        if self.sr is None:
            return []

        try:
            mic_list = self.sr.Microphone.list_microphone_names()
            return [(i, name) for i, name in enumerate(mic_list)]
        except (OSError, AttributeError):
            return []

    def listen(self, device_index: int | None = None) -> tuple[bytes, str]:
        """Record audio from microphone.

        Args:
            device_index: Specific microphone device index to use

        Returns:
            Tuple of (audio_data, temp_file_path)

        Raises:
            RuntimeError: If microphone is not available
        """
        if not self.is_available():
            raise RuntimeError("Microphone not available. Please check your audio devices.")

        recognizer = self.sr.Recognizer()

        # Configure microphone
        mic_kwargs = {}
        if device_index is not None:
            mic_kwargs["device_index"] = device_index

        try:
            with self.sr.Microphone(**mic_kwargs) as source:
                # Adjust for ambient noise
                print("🎤 Adjusting for ambient noise... (请稍候)")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("🎤 Listening... (请说话)")

                # Listen with automatic silence detection
                audio_data = recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_threshold
                )

                print("✅ Audio captured!")

                # Save to temporary WAV file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    delete=False,
                    mode="wb"
                )
                temp_file_path = temp_file.name
                temp_file.close()

                # Write audio data to WAV file
                with wave.open(temp_file_path, "wb") as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
                    wav_file.setframerate(16000)  # 16kHz sample rate for Whisper

                    # Get raw audio data from speech_recognition AudioData
                    wav_file.writeframes(audio_data.get_wav_data())

                return (audio_data.get_wav_data(), temp_file_path)

        except self.sr.WaitTimeoutError:
            raise RuntimeError("No speech detected. Please try again.")
        except OSError as e:
            raise RuntimeError(f"Microphone error: {e}")

    async def transcribe(self, audio_file_path: str) -> str:
        """Transcribe audio to text using OpenAI Whisper API.

        Args:
            audio_file_path: Path to audio file

        Returns:
            Transcribed text

        Raises:
            RuntimeError: If transcription fails
        """
        api_key = self.OPENAI_API_KEY
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Please set it in your environment "
                "to use voice transcription."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        # Prepare the file for upload
        try:
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "file": (audio_file_path, audio_file, "audio/wav"),
                }
                data = {
                    "model": "whisper-1",
                    "language": "zh",  # Default to Chinese, auto-detects if not specified
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.WHISPER_API_URL,
                        headers=headers,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    result = response.json()
                    return result.get("text", "").strip()

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "No response"
            raise RuntimeError(f"Transcription API error: {e} - {error_detail}")
        except FileNotFoundError:
            raise RuntimeError(f"Audio file not found: {audio_file_path}")
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    async def listen_and_transcribe(self, device_index: int | None = None) -> str:
        """Record audio and transcribe to text in one step.

        Args:
            device_index: Specific microphone device index to use

        Returns:
            Transcribed text
        """
        audio_data, temp_file = self.listen(device_index)
        try:
            text = await self.transcribe(temp_file)
            return text
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    def listen_and_transcribe_sync(self, device_index: int | None = None) -> str:
        """Synchronous version of listen_and_transcribe.

        Args:
            device_index: Specific microphone device index to use

        Returns:
            Transcribed text
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.listen_and_transcribe(device_index))


def get_default_voice_listener() -> VoiceListener:
    """Get a configured VoiceListener instance.

    Returns:
        VoiceListener instance with default settings
    """
    return VoiceListener(timeout=5, phrase_threshold=10)
