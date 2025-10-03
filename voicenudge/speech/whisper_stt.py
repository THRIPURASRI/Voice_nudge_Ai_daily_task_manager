import os
import whisper

# Load Whisper model (tiny, base, small, medium, large)
model_size = os.getenv("WHISPER_MODEL", "small")
model = whisper.load_model(model_size)

def transcribe_audio(audio_file_path: str, translate: bool = True) -> str:
    """
    Converts speech into text using Whisper.
    If translate=True → translates into English.
    If translate=False → keeps original language transcription.
    """
    task_type = "translate" if translate else "transcribe"
    result = model.transcribe(audio_file_path, task=task_type)
    return result["text"]
