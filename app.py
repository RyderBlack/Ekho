from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from gradio_client import Client, handle_file
import os
from dotenv import load_dotenv
from google_auth import get_google_credentials, get_user_info, read_spreadsheet, upload_spreadsheet
import pandas as pd
import re
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)  # Required for session
CORS(app)

# OAuth 2.0 configuration
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

def get_hf_token():
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN not found in .env file")
    return token

@app.route('/')
def index():
    if 'user' not in session:
        return send_from_directory('static', 'login.html')
    if 'spreadsheet_id' not in session:
        return redirect(url_for('select_spreadsheet_page'))
    return send_from_directory('static', 'index.html')

@app.route('/select-spreadsheet-page')
def select_spreadsheet_page():
    if 'user' not in session:
        return redirect(url_for('index'))
    return send_from_directory('static', 'select_spreadsheet.html')

@app.route('/auth/google')
def google_auth():
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=url_for('oauth2callback', _external=True)
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to ensure we get refresh token
        )
        session['state'] = state
        return jsonify({'auth_url': authorization_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/auth/google/callback')
def oauth2callback():
    try:
        state = session['state']
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=url_for('oauth2callback', _external=True)
        )
        
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # Get user info
        user_info = get_user_info(credentials)
        session['user'] = user_info
        session['creds'] = credentials.to_json()
        
        return redirect(url_for('select_spreadsheet_page'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-access-token')
def get_access_token():
    if 'creds' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        creds = Credentials.from_authorized_user_info(json.loads(session['creds']))
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                session['creds'] = creds.to_json()
        return jsonify({'access_token': creds.token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/select-spreadsheet-file/<file_id>')
def select_spreadsheet_file(file_id):
    if 'creds' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        creds = Credentials.from_authorized_user_info(json.loads(session['creds']))
        service = build('drive', 'v3', credentials=creds)
        
        try:
            # Get file metadata
            file_metadata = service.files().get(
                fileId=file_id,
                fields='name,mimeType'
            ).execute()
            
            mime_type = file_metadata.get('mimeType', '')
            
            if mime_type == 'application/vnd.google-apps.spreadsheet':
                # It's a Google Sheets file
                sheets_service = build('sheets', 'v4', credentials=creds)
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=file_id,
                    range='A:B'  # Read first two columns
                ).execute()
                
                values = result.get('values', [])
                if not values or len(values) < 2:  # Need at least header and one row
                    return jsonify({'error': 'Le fichier est vide ou mal formaté'}), 400
                
                # Skip header row and store first name and last name pairs
                names = [(row[0], row[1]) for row in values[1:] if len(row) >= 2]
            else:
                # It's a regular spreadsheet file (Excel, CSV, etc.)
                request = service.files().get_media(fileId=file_id)
                file_content = request.execute()
                
                # Save to temporary file
                temp_path = os.path.join('static', 'temp', file_metadata['name'])
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, 'wb') as f:
                    f.write(file_content)
                
                try:
                    # Read the file based on its extension
                    if file_metadata['name'].endswith('.csv'):
                        df = pd.read_csv(temp_path)
                    else:
                        df = pd.read_excel(temp_path)
                    
                    if len(df.columns) < 2:
                        raise ValueError("Spreadsheet must have at least two columns")
                    
                    # Store first name and last name pairs
                    names = list(zip(df.iloc[:, 0], df.iloc[:, 1]))
                finally:
                    # Clean up
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            if not names:
                return jsonify({'error': 'Le fichier est vide'}), 400
            
            # Store the spreadsheet ID and data in session
            session['spreadsheet_id'] = file_id
            session['spreadsheet_data'] = names
            
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error accessing file: {str(e)}")  # Debug log
            return jsonify({'error': f'Impossible d\'accéder au fichier: {str(e)}'}), 400
            
    except Exception as e:
        print(f"Error in select_spreadsheet_file: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/upload-spreadsheet', methods=['POST'])
def upload_spreadsheet_route():
    if 'creds' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Save file temporarily
        temp_path = os.path.join('static', 'temp', file.filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        file.save(temp_path)
        
        # Read the spreadsheet to verify it's valid
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            else:
                df = pd.read_excel(temp_path)
            
            # Ensure the first column exists and contains names
            if len(df.columns) == 0:
                raise ValueError("Spreadsheet is empty")
            
            # Store the data in session
            session['spreadsheet_data'] = df.iloc[:, 0].tolist()  # Store first column as list
            session['spreadsheet_id'] = 'local_file'  # Mark as local file
            
            # Clean up
            os.remove(temp_path)
            
            return jsonify({'success': True, 'redirect': url_for('index')})
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': f'Format de fichier invalide: {str(e)}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Extract name from transcription
        name_match = re.search(r"mon nom est (.+)", result.lower())
        if name_match:
            spoken_name = name_match.group(1).strip()
            spoken_parts = spoken_name.split()
            
            # Check if name exists in spreadsheet
            if 'spreadsheet_data' in session:
                names = session['spreadsheet_data']
                for first_name, last_name in names:
                    # Convert all to lowercase for comparison
                    first_name_lower = str(first_name).lower()
                    last_name_lower = str(last_name).lower()
                    spoken_parts_lower = [part.lower() for part in spoken_parts]
                    
                    # Check if both first name and last name are present in the spoken name
                    if (first_name_lower in spoken_parts_lower and 
                        last_name_lower in spoken_parts_lower):
                        # Capitalize both names
                        capitalized_first = first_name.capitalize()
                        capitalized_last = last_name.capitalize()
                        return jsonify({
                            'transcription': result,
                            'welcome_message': f"Bienvenue à La Plateforme_ {capitalized_first} {capitalized_last}"
                        })
            
            return jsonify({
                'transcription': result,
                'welcome_message': f"Nom non reconnu: {spoken_name}"
            })
        
        return jsonify({'transcription': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development
    app.run(debug=True, port=5000) 