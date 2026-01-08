## 🎧 Insurance Call Assistant (Streamlit + Python)

Transcribe insurance support calls, generate concise summaries, extract caller details (name, mobile number, submission number), and look up submission details from a sample dataset.

### Features
- Upload audio (WAV/MP3/M4A) and get high-quality transcription (OpenAI).
- Structured summary of the conversation.
- Extracts caller details into a clean JSON schema.
- Confirm/correct details via a form and fetch submission info (mock dataset).

### Tech
- Streamlit UI
- OpenAI GPT models (`gpt-4o-mini-transcribe`, `gpt-4o-mini`) or Google Gemini (`gemini-1.5-flash`)
- Python services for transcription, summarization, extraction
- CSV-based mock submissions dataset (easily swappable for an API or DB)
- Optional Flask + Twilio backend for outbound/inbound calls and recording

---

### Setup
1) Python 3.10+ recommended

2) Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows PowerShell
```

3) Install dependencies:
```bash
pip install -r requirements.txt
```

4) Set environment variables:
- Copy `ENV_EXAMPLE.txt` → create `.env` in project root and add your key(s)
  - `OPENAI_API_KEY=...` (for OpenAI)
  - `GOOGLE_API_KEY=...` (for Gemini)
  - Optional overrides:
    - `TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe`
    - `CHAT_MODEL=gpt-4o-mini`
    - `GEMINI_TRANSCRIPTION_MODEL=gemini-1.5-flash`
    - `GEMINI_CHAT_MODEL=gemini-1.5-flash`
    - `PROVIDER=openai` or `gemini`

You can also paste your key into the Streamlit sidebar if you prefer not to use `.env`.

5) Run the app:
```bash
streamlit run app.py
```

6) (Optional) Run Flask + Twilio backend:
```bash
export FLASK_APP=flask_app.py  # PowerShell: $env:FLASK_APP = "flask_app.py"
flask run --port 5001
```
Configure in `.env`:
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_CALLER_ID`
- `PUBLIC_BASE_URL` (reachable URL Twilio can call, e.g. from ngrok)
- `CALL_BACKEND_URL` (Streamlit → Flask, e.g. `http://localhost:5001`)

### Usage
1. Upload a call recording (or paste a transcript).
2. Pick provider (OpenAI or Gemini) and set API key if not already configured.
3. Click “Transcribe Audio” → “Summarize” → “Extract Details” (or use “Run All”).
4. Confirm/correct extracted details in the form and click “Find Submission”.
5. (Optional Twilio flow) Use the “Outbound Call (Twilio demo)” section:
   - Start a call to the customer via Twilio.
   - After hangup, use the Call SID to fetch transcript, summary, extracted details, and matched submission.

### Customization
- Replace `data/submissions.csv` with your own export or wire in your API/DB:
  - Update `services/submissions.py` to call your backend.
- For call capture/telephony integration:
  - This repo includes a simple Twilio + Flask example for outbound/inbound calls.
  - For production, secure the Flask endpoints, persist call results, and move secrets to a proper secret manager.

### Notes
- This project uses OpenAI’s latest Python SDK and models. Ensure your account has access.
- If you encounter transcription issues, try using WAV 16kHz mono or clear MP3 recordings.


