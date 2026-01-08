import os
from io import BytesIO
from typing import Any, Dict

import requests
from flask import Flask, jsonify, request, Response
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from config import get_env, get_provider
from models import ExtractedInfo
from services.submissions import find_submission
from services.summarize import extract_caller_info, summarize_transcript
from services.transcribe import transcribe_audio

app = Flask(__name__)


CALL_RESULTS: Dict[str, Dict[str, Any]] = {}


def get_twilio_client() -> Client:
    account_sid = get_env("TWILIO_ACCOUNT_SID")
    auth_token = get_env("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        raise RuntimeError("TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set")
    return Client(account_sid, auth_token)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/call/start")
def start_call() -> Response:
    """Start an outbound call via Twilio and record it.

    Expects JSON: {"to": "+91..."}
    """
    data = request.get_json(force=True, silent=True) or {}
    to_number = data.get("to")
    if not to_number:
        return jsonify({"error": "Missing 'to' phone number"}), 400

    from_number = get_env("TWILIO_CALLER_ID")
    public_base_url = get_env("PUBLIC_BASE_URL")
    if not from_number or not public_base_url:
        return (
            jsonify(
                {
                    "error": "TWILIO_CALLER_ID or PUBLIC_BASE_URL not set in environment.",
                    "hint": "Set your Twilio phone number as TWILIO_CALLER_ID and your public URL as PUBLIC_BASE_URL.",
                }
            ),
            500,
        )

    client = get_twilio_client()
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url=f"{public_base_url}/twilio/voice",
    )

    return jsonify({"call_sid": call.sid})


@app.post("/twilio/voice")
def twilio_voice() -> Response:
    """TwiML for inbound/outbound calls.

    For simplicity, this plays a short message and records the call.
    After hangup, Twilio will POST to /twilio/recording with the recording URL.
    """
    public_base_url = get_env("PUBLIC_BASE_URL") or ""
    recording_callback = f"{public_base_url}/twilio/recording" if public_base_url else ""

    vr = VoiceResponse()
    vr.say("Thank you for calling. This call will be recorded for quality and training purposes.")
    vr.record(
        max_length="600",
        play_beep=True,
        recording_status_callback=recording_callback or None,
        recording_status_callback_method="POST",
    )
    vr.say("Goodbye.")

    return Response(str(vr), mimetype="text/xml")


@app.post("/twilio/recording")
def twilio_recording() -> Response:
    """Handles Twilio recording status callback, downloads audio, and runs the pipeline."""
    recording_url = request.form.get("RecordingUrl")
    call_sid = request.form.get("CallSid")

    if not recording_url or not call_sid:
        return ("Missing RecordingUrl or CallSid", 400)

    # Twilio RecordingUrl does not include extension; append .wav for a WAV file
    audio_url = f"{recording_url}.wav"
    resp = requests.get(audio_url, stream=True, timeout=60)
    resp.raise_for_status()

    audio_bytes = BytesIO(resp.content)

    provider = get_provider()
    api_key_env = "OPENAI_API_KEY" if provider == "openai" else "GOOGLE_API_KEY"
    api_key = os.getenv(api_key_env)

    # Run existing pipeline
    transcript = transcribe_audio(audio_bytes, provider=provider, api_key=api_key)
    summary = summarize_transcript(transcript, provider=provider, api_key=api_key)
    extracted: ExtractedInfo = extract_caller_info(transcript, provider=provider, api_key=api_key)
    submission = find_submission(extracted)

    CALL_RESULTS[call_sid] = {
        "transcript": transcript,
        "summary": summary,
        "extracted": extracted.model_dump(),
        "submission": submission,
    }

    return ("", 204)


@app.get("/call/result/<call_sid>")
def call_result(call_sid: str) -> Response:
    """Return processed call results (if available)."""
    result = CALL_RESULTS.get(call_sid)
    if not result:
        return jsonify({"status": "pending", "call_sid": call_sid}), 404
    return jsonify({"status": "ready", "call_sid": call_sid, **result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_PORT", "5001")), debug=True)


