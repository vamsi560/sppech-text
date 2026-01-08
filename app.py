import os
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from config import get_default_models, get_provider, load_env_if_present
from models import ExtractedInfo
from services.submissions import find_submission
from services.summarize import extract_caller_info, summarize_transcript
from services.transcribe import transcribe_audio


def set_api_key_from_ui(provider: str, user_key: Optional[str]) -> None:
    if not user_key:
        return
    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = user_key
    elif provider == "gemini":
        os.environ["GOOGLE_API_KEY"] = user_key


def main() -> None:
    load_env_if_present()
    st.set_page_config(page_title="Insurance Call Assistant", page_icon="🎧", layout="wide")
    st.title("🎧 Insurance Call Assistant")
    st.caption("Transcribe calls, summarize, extract caller details, and fetch submission info.")

    with st.sidebar:
        st.subheader("Configuration")
        provider = st.selectbox("Provider", options=["openai", "gemini"], index=0 if get_provider() == "openai" else 1)
        key_label = "OpenAI API Key" if provider == "openai" else "Google API Key"
        ui_key = st.text_input(
            key_label,
            type="password",
            help="If not set in environment, paste your key here.",
            value=os.getenv("OPENAI_API_KEY" if provider == "openai" else "GOOGLE_API_KEY", ""),
        )
        set_api_key_from_ui(provider, ui_key or None)

        models = get_default_models(provider)
        st.write("Models")
        st.code(
            f"Transcription: {models['transcription_model']}\nChat: {models['chat_model']}",
            language="text",
        )

        st.markdown("---")
        st.markdown(
            "Need help? Ensure your API key is set. Audio formats like WAV/MP3/M4A work best."
        )

    if "transcript_text" not in st.session_state:
        st.session_state["transcript_text"] = ""
    if "summary_text" not in st.session_state:
        st.session_state["summary_text"] = ""
    if "extracted_info" not in st.session_state:
        st.session_state["extracted_info"] = ExtractedInfo()

    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("1) Provide Call Audio or Paste Transcript")
        uploaded = st.file_uploader(
            "Upload call recording (WAV/MP3/M4A)",
            type=["wav", "mp3", "m4a"],
            accept_multiple_files=False,
        )
        st.write("Or paste transcript text:")
        transcript_input = st.text_area(
            "Transcript",
            value=st.session_state["transcript_text"],
            height=150,
            placeholder="Paste transcript here (optional if audio is uploaded)",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Transcribe Audio"):
                if not uploaded:
                    st.warning("Please upload an audio file first.")
                else:
                    with st.spinner("Transcribing audio..."):
                        try:
                            st.session_state["transcript_text"] = transcribe_audio(uploaded, provider=provider, api_key=ui_key or None)
                            st.success("Transcription complete.")
                        except Exception as e:
                            st.error(f"Transcription failed: {e}")

        with col_b:
            if st.button("Summarize"):
                text = transcript_input.strip() or st.session_state["transcript_text"].strip()
                if not text:
                    st.warning("Provide transcript text or transcribe from audio first.")
                else:
                    with st.spinner("Summarizing..."):
                        try:
                            st.session_state["summary_text"] = summarize_transcript(text, provider=provider, api_key=ui_key or None)
                            st.success("Summary generated.")
                        except Exception as e:
                            st.error(f"Summarization failed: {e}")

        with col_c:
            if st.button("Extract Details"):
                text = transcript_input.strip() or st.session_state["transcript_text"].strip()
                if not text:
                    st.warning("Provide transcript text or transcribe from audio first.")
                else:
                    with st.spinner("Extracting details..."):
                        try:
                            st.session_state["extracted_info"] = extract_caller_info(text, provider=provider, api_key=ui_key or None)
                            st.success("Details extracted.")
                        except Exception as e:
                            st.error(f"Extraction failed: {e}")

        # Run All convenience
        if st.button("Run All (Transcribe → Summarize → Extract)"):
            try:
                # If transcript empty and audio provided, transcribe first
                if not transcript_input.strip() and uploaded:
                    with st.spinner("Transcribing audio..."):
                        st.session_state["transcript_text"] = transcribe_audio(uploaded, provider=provider, api_key=ui_key or None)
                text = transcript_input.strip() or st.session_state["transcript_text"].strip()
                if not text:
                    st.warning("No audio or transcript provided.")
                else:
                    with st.spinner("Summarizing..."):
                        st.session_state["summary_text"] = summarize_transcript(text, provider=provider, api_key=ui_key or None)
                    with st.spinner("Extracting details..."):
                        st.session_state["extracted_info"] = extract_caller_info(text, provider=provider, api_key=ui_key or None)
                    st.success("Completed all steps.")
            except Exception as e:
                st.error(f"Pipeline failed: {e}")

        if st.session_state["transcript_text"] or transcript_input.strip():
            with st.expander("Transcript", expanded=False):
                st.text_area(
                    "Transcript output",
                    value=transcript_input.strip() or st.session_state["transcript_text"],
                    height=220,
                )

        if st.session_state["summary_text"]:
            st.subheader("Summary")
            st.write(st.session_state["summary_text"])

    with right:
        st.subheader("2) Caller Details")
        extracted: ExtractedInfo = st.session_state["extracted_info"]
        with st.form("confirm_details"):
            name = st.text_input("Name", value=extracted.name or "")
            mobile = st.text_input("Mobile Number", value=extracted.mobile_number or "")
            submission = st.text_input("Submission Number", value=extracted.submission_number or "")
            submitted = st.form_submit_button("Find Submission")

        if submitted:
            confirmed = ExtractedInfo(name=name or None, mobile_number=mobile or None, submission_number=submission or None)
            with st.spinner("Searching submissions..."):
                match = find_submission(confirmed)
            if match:
                st.success("Submission found.")
                st.dataframe(pd.DataFrame([match]))
            else:
                st.warning("No matching submission found. Adjust details and try again.")

        st.markdown("---")
        st.caption(
            "Tip: If name/mobile/submission aren't mentioned in the call, ask the caller and enter them here."
        )

        st.subheader("3) Outbound Call (Twilio demo)")
        backend_url = os.getenv("CALL_BACKEND_URL", "https://sppech-text.onrender.com")
        st.code(f"Backend URL: {backend_url}", language="text")
        to_number = st.text_input("Customer Phone (E.164 format)", value="")
        if st.button("Start Outbound Call via Twilio"):
            if not to_number:
                st.warning("Enter a customer phone number.")
            else:
                try:
                    with st.spinner("Starting call via Twilio..."):
                        resp = requests.post(f"{backend_url}/call/start", json={"to": to_number}, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"Call started. Call SID: {data.get('call_sid')}")
                        st.info("After hangup, use the Call SID below to fetch transcript and summary.")
                    else:
                        st.error(f"Failed to start call: {resp.text}")
                except Exception as e:
                    st.error(f"Error calling backend: {e}")

        call_sid_lookup = st.text_input("Existing Call SID to fetch results", value="")
        if st.button("Fetch Call Result"):
            if not call_sid_lookup:
                st.warning("Enter a Call SID.")
            else:
                try:
                    with st.spinner("Fetching call result..."):
                        resp = requests.get(f"{backend_url}/call/result/{call_sid_lookup}", timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success("Call result ready.")
                        st.session_state["transcript_text"] = data.get("transcript", "")
                        st.session_state["summary_text"] = data.get("summary", "")
                        extracted_data = data.get("extracted") or {}
                        st.session_state["extracted_info"] = ExtractedInfo(**extracted_data)
                        submission = data.get("submission")
                        if submission:
                            st.markdown("**Matched Submission from Call:**")
                            st.dataframe(pd.DataFrame([submission]))
                    else:
                        st.warning(f"Result not ready or not found: {resp.text}")
                except Exception as e:
                    st.error(f"Error fetching result: {e}")


if __name__ == "__main__":
    main()


