from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gradio_client import Client, handle_file
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

def get_hf_token():
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN not found in .env file")
    return token

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        temp_path = os.path.join('static', 'temp', audio_file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        audio_file.save(temp_path)
        
        client = Client(
            "hf-audio/whisper-large-v3-turbo",
            hf_token=get_hf_token()
        )
        
        result = client.predict(
            inputs=handle_file(temp_path),
            task="transcribe",
            api_name="/predict"
        )
        
        # Clean up temporary file
        os.remove(temp_path)
        
        return jsonify({'transcription': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 