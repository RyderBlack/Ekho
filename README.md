# EKHO - AI Vocal Assistant

Ekho is an AI-powered vocal assistant designed for event attendance tracking. By pressing the voice button, Ekho listens for a participant's name, recognizes it using speech-to-text, and automatically adds that person to the event's attendance sheet — no manual input required.

## Demo

**Usage Demo**

![Usage Demo](https://github.com/RyderBlack/Ekho/blob/main/assets/Ekho_video_demo.gif?raw=true)

**Success Demo**

https://github.com/user-attachments/assets/08ff81db-4d2f-42c7-876c-9bcd8439ff72

## Installation

1. Clone the repository:
```bash
git clone https://github.com/RyderBlack/Ekho.git
cd Ekho
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables by creating a `.env` file at the root of the project:
```
GOOGLE_CREDENTIALS=your_google_service_account_json
SPREADSHEET_ID=your_google_spreadsheet_id
```

## Usage

1. Launch the app:
```bash
python app.py
```

2. Open the interface in your browser.

3. Press the **voice button** and clearly say the participant's name.

4. Ekho will recognize the name and automatically add it to the attendance sheet linked to the current event.

## Notes

- Make sure you have a stable internet connection — the speech recognition model runs on Hugging Face's servers.
- The attendance sheet is managed via Google Sheets; ensure your service account has edit access to the spreadsheet.
