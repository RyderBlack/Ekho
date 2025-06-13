import gradio as gr
from gradio_client import Client, handle_file
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

def get_hf_token():
    """
    Get Hugging Face token from .env file
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN not found in .env file. Please add your Hugging Face token to the .env file.")
    return token

def transcribe_audio(audio_file, task="transcribe"):
    """
    Transcribe an audio file using the Whisper API
    """
    try:
        client = Client(
            "hf-audio/whisper-large-v3-turbo",
            hf_token=get_hf_token()
        )
        result = client.predict(
            inputs=handle_file(audio_file),
            task=task,
            api_name="/predict"
        )
        return result
    except Exception as e:
        return f"Error in transcription: {str(e)}"

def create_interface():
    """
    Create the Gradio interface
    """
    with gr.Blocks(title="Ekho", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# Ekho")
        
        # Instructions
        gr.Markdown("""
        ### Instructions
        Pour commencer, cliquez sur le bouton vert "Start" et dites :
        "Mon nom est [votre nom]"
        
        Cliquez sur "Stop" lorsque vous avez terminé.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                # Audio input (hidden)
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    visible=False
                )
                
                # Start/Stop button
                start_stop_btn = gr.Button(
                    "Start",
                    variant="primary",
                    size="lg"
                )
                
                # Output text
                output_text = gr.Textbox(
                    label="Transcription",
                    placeholder="Votre transcription apparaîtra ici...",
                    lines=3
                )
        
        # State to track recording status
        is_recording = gr.State(False)
        
        def toggle_recording():
            if not is_recording.value:
                # Start recording
                is_recording.value = True
                return "Stop", gr.update(variant="stop")
            else:
                # Stop recording
                is_recording.value = False
                return "Start", gr.update(variant="primary")
        
        def on_stop(audio):
            if audio is not None:
                return transcribe_audio(audio)
            return "Aucun enregistrement trouvé."
        
        # Set up the button click action
        start_stop_btn.click(
            fn=toggle_recording,
            inputs=[],
            outputs=[start_stop_btn, start_stop_btn]
        ).then(
            fn=lambda: None,
            inputs=[],
            outputs=audio_input
        ).then(
            fn=on_stop,
            inputs=[audio_input],
            outputs=output_text
        )
    
    return interface

if __name__ == "__main__":
    # Verify token is available before starting
    get_hf_token()
    interface = create_interface()
    interface.launch(share=True) 