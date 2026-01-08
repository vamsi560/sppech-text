from typing import Optional
from config import (
    get_default_models,
    configure_gemini_client,
    get_provider,
)
from models import ExtractedInfo
import google.generativeai as genai

def _summarize_gemini(transcript_text: str, model: str, api_key: Optional[str]) -> str:
    configure_gemini_client(api_key)
    gemini_model = genai.GenerativeModel(model)
    prompt = (
        "Summarize this insurance support call. "
        "Return a short, structured summary with: Purpose, Key details (bullets), "
        "Customer sentiment, Next steps. Avoid hallucinating."
    )
    response = gemini_model.generate_content(
        [prompt, f"Transcript:\n\n{transcript_text}"],
        generation_config={"temperature": 0.2},
    )
    return (response.text or "").strip()

def summarize_transcript(
    transcript_text: str,
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    if not transcript_text.strip():
        return ""
    provider = provider or get_provider()
    models = get_default_models(provider)
    chat_model = model or models["chat_model"]
    if provider != "gemini":
        raise RuntimeError("Only Gemini provider is supported in this deployment.")
    return _summarize_gemini(transcript_text, chat_model, api_key)

def _extract_gemini(transcript_text: str, model: str, api_key: Optional[str]) -> ExtractedInfo:
    configure_gemini_client(api_key)
    gemini_model = genai.GenerativeModel(model)
    prompt = (
        "Extract caller details from the transcript. "
        "Return JSON with keys exactly: name, mobile_number, submission_number. "
        "Use null when unknown. Do not invent details."
    )
    response = gemini_model.generate_content(
        [prompt, f"Transcript:\n\n{transcript_text}"],
        generation_config={"temperature": 0},
    )
    content = response.text or ""
    return ExtractedInfo.model_validate_json(content)

def extract_caller_info(
    transcript_text: str,
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
) -> ExtractedInfo:
    if not transcript_text.strip():
        return ExtractedInfo()
    provider = provider or get_provider()
    models = get_default_models(provider)
    chat_model = model or models["chat_model"]
    if provider != "gemini":
        raise RuntimeError("Only Gemini provider is supported in this deployment.")
    try:
        return _extract_gemini(transcript_text, chat_model, api_key)
    except Exception:
        return ExtractedInfo()


