import os
from faster_whisper import WhisperModel

# Model sizes:
# tiny, base, small, medium, large-v3

MODEL_NAME = os.getenv("WHISPER_MODEL", "base")

_model = None


def transcribe(audio_path: str) -> str:
    """
    Transcribe an audio file using Faster-Whisper.
    Returns the transcription as a string.
    """
    model = _get_model()

    segments, info = model.transcribe(
        audio_path,
        beam_size=5
    )

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text.strip()


def _get_model():
    global _model

    if _model is None:
        _model = WhisperModel(
            MODEL_NAME,
            device="cpu",          # Change to "cuda" if using an NVIDIA GPU
            compute_type="int8"    # Efficient for CPU
        )

    return _model