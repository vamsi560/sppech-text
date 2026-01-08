from typing import Optional

import google.generativeai as genai

from config import (
    configure_gemini_client,
    get_default_models,
    get_openai_client,
    get_provider,
)
from models import ExtractedInfo


def _summarize_openai(transcript_text: str, model: str, api_key: Optional[str]) -> str:
    client = get_openai_client(api_key)
    system_prompt = (
        "You are an assistant that summarizes insurance support calls clearly and concisely. "
        "Write a short, structured summary with: Purpose, Key details (bullets), "
        "Customer sentiment, and Next steps. Avoid hallucinating."
    )
    user_prompt = f"Transcript:\n\n{transcript_text}"
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content.strip()


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

    if provider == "openai":
        return _summarize_openai(transcript_text, chat_model, api_key)
    if provider == "gemini":
        return _summarize_gemini(transcript_text, chat_model, api_key)
    raise RuntimeError(f"Unsupported provider '{provider}'")


def _extract_openai(transcript_text: str, model: str, api_key: Optional[str]) -> ExtractedInfo:
    client = get_openai_client(api_key)
    system_prompt = (
        "Extract caller details from the transcript. "
        "Return a JSON object with keys: name, mobile_number, submission_number. "
        "If unknown, use null. Do not invent details."
    )
    user_prompt = f"Transcript:\n\n{transcript_text}"
    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = resp.choices[0].message.content
    return ExtractedInfo.model_validate_json(content)


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
    try:
        if provider == "openai":
            return _extract_openai(transcript_text, chat_model, api_key)
        if provider == "gemini":
            return _extract_gemini(transcript_text, chat_model, api_key)
    except Exception:
        # Fallback to empty if parsing fails
        return ExtractedInfo()
    raise RuntimeError(f"Unsupported provider '{provider}'")


