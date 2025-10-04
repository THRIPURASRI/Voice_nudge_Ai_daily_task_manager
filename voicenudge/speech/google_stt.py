import io
from google.cloud import speech

client = speech.SpeechClient()

def transcribe_audio_google(audio_file_path: str, language_code="en-US") -> str:
    with io.open(audio_file_path, "rb") as f:
        content = f.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
        enable_automatic_punctuation=True,
    )

    response = client.recognize(config=config, audio=audio)

    results = [r.alternatives[0].transcript for r in response.results]
    return " ".join(results)
