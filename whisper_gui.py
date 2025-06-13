import gradio as gr
from gradio_client import Client, handle_file
import os
import tempfile

def transcribe_audio(audio_file, task="transcribe"):
    """
    Transcribe an audio file using the Whisper API
    """
    try:
        client = Client("hf-audio/whisper-large-v3-turbo")
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
    with gr.Blocks(title="Whisper Transcription", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎤 Whisper Large V3 Turbo Transcription")
        gr.Markdown("Record your voice or upload an audio file to transcribe it.")
        
        with gr.Row():
            with gr.Column():
                # Audio input
                audio_input = gr.Audio(
                    sources=["microphone", "upload"],
                    type="filepath",
                    label="Record or Upload Audio"
                )
                
                # Task selection
                task = gr.Radio(
                    choices=["transcribe", "translate"],
                    value="transcribe",
                    label="Task"
                )
                
                # Submit button
                submit_btn = gr.Button("Transcribe", variant="primary")
            
            with gr.Column():
                # Output text
                output_text = gr.Textbox(
                    label="Transcription",
                    placeholder="Transcription will appear here...",
                    lines=5
                )
        
        # Set up the submit action
        submit_btn.click(
            fn=transcribe_audio,
            inputs=[audio_input, task],
            outputs=output_text
        )
        
        # Examples
        gr.Examples(
            examples=[
                ["https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav", "transcribe"],
            ],
            inputs=[audio_input, task],
            outputs=output_text,
            fn=transcribe_audio,
            cache_examples=True,
        )
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(share=True) 