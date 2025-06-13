from gradio_client import Client, handle_file
import os
import pyaudio
import wave
import time

def record_audio(filename="recording.wav", duration=5):
    """
    Record audio from microphone for specified duration
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    print(f"Recording for {duration} seconds...")
    
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    for i in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording finished!")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return filename

def transcribe_audio_file(audio_file_path, task="transcribe"):
    """
    Transcribe an audio file using the first API endpoint (/predict)
    """
    try:
        client = Client("hf-audio/whisper-large-v3-turbo")
        result = client.predict(
            inputs=handle_file(audio_file_path),
            task=task,
            api_name="/predict"
        )
        return result
    except Exception as e:
        return f"Error in transcribe_audio_file: {str(e)}"

def transcribe_audio_file_alt(audio_file_path, task="transcribe"):
    """
    Transcribe an audio file using the second API endpoint (/predict_1)
    """
    try:
        client = Client("hf-audio/whisper-large-v3-turbo")
        result = client.predict(
            inputs=handle_file(audio_file_path),
            task=task,
            api_name="/predict_1"
        )
        return result
    except Exception as e:
        return f"Error in transcribe_audio_file_alt: {str(e)}"

def transcribe_youtube_url(youtube_url, task="transcribe"):
    """
    Transcribe audio from a YouTube URL using the third API endpoint (/predict_2)
    """
    try:
        client = Client("hf-audio/whisper-large-v3-turbo")
        result = client.predict(
            yt_url=youtube_url,
            task=task,
            api_name="/predict_2"
        )
        return result
    except Exception as e:
        return f"Error in transcribe_youtube_url: {str(e)}"

def main():
    print("Whisper Large V3 Turbo Demo")
    print("-" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Record and transcribe")
        print("2. Exit")
        
        choice = input("\nEnter your choice (1-2): ")
        
        if choice == "1":
            duration = int(input("Enter recording duration in seconds (default 5): ") or "5")
            filename = record_audio(duration=duration)
            
            print("\nTranscribing your recording...")
            result = transcribe_audio_file(filename)
            print(f"\nTranscription: {result}")
            
            # Ask if user wants to keep the recording
            keep = input("\nDo you want to keep the recording? (y/n): ").lower()
            if keep != 'y':
                os.remove(filename)
                print("Recording deleted.")
                
        elif choice == "2":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 