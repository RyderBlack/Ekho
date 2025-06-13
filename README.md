# Whisper Large V3 Turbo Demo

This project demonstrates how to use the Hugging Face Whisper Large V3 Turbo model for audio transcription and translation.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The script provides three main functions:

1. `transcribe_audio_file(audio_file_path, task="transcribe")`: Transcribes a local audio file
2. `transcribe_audio_file_alt(audio_file_path, task="transcribe")`: Alternative method to transcribe a local audio file
3. `transcribe_youtube_url(youtube_url, task="transcribe")`: Transcribes audio from a YouTube URL

The `task` parameter can be either:
- `"transcribe"`: Transcribes the audio in its original language
- `"translate"`: Translates the audio to English

### Example

```python
from whisper_demo import transcribe_audio_file, transcribe_youtube_url

# Transcribe a local audio file
result = transcribe_audio_file("path/to/your/audio.wav")
print(result)

# Transcribe a YouTube video
result = transcribe_youtube_url("https://www.youtube.com/watch?v=example")
print(result)
```

## Notes

- Make sure you have a stable internet connection as the model runs on Hugging Face's servers
- The script handles errors gracefully and will return error messages if something goes wrong
- For YouTube URLs, make sure the video is publicly accessible 