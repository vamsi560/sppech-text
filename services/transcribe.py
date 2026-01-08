from typing import Optional, BinaryIO

import google.generativeai as genai

from config import (
    configure_gemini_client,
    get_default_models,
    get_openai_client,
    get_provider,
)


def _transcribe_openai(file_obj: BinaryIO, model: str, api_key: Optional[str]) -> str:
    client = get_openai_client(api_key)
    file_obj.seek(0)
    result = client.audio.transcriptions.create(
        model=model,
        file=file_obj,
    )
    return getattr(result, "text", "").strip()


def _transcribe_gemini(file_obj: BinaryIO, model: str, api_key: Optional[str]) -> str:
    configure_gemini_client(api_key)
    file_obj.seek(0)
    data = file_obj.read()
    mime_type = getattr(file_obj, "type", None) or "audio/wav"
    gemini_model = genai.GenerativeModel(model)
    response = gemini_model.generate_content(
        [
            {"mime_type": mime_type, "data": data},
            "Transcribe this insurance support call. Return only the transcript text without timestamps.",
        ],
        generation_config={"temperature": 0},
    )
    return (response.text or "").strip()


def transcribe_audio(
    file_obj: BinaryIO,
    *,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    provider = provider or get_provider()
    models = get_default_models(provider)
    transcription_model = model or models["transcription_model"]

    if provider == "openai":
        return _transcribe_openai(file_obj, transcription_model, api_key)
    if provider == "gemini":
        return _transcribe_gemini(file_obj, transcription_model, api_key)
    raise RuntimeError(f"Unsupported provider '{provider}'")


