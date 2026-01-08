import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

SUPPORTED_PROVIDERS = ("openai", "gemini")


def load_env_if_present() -> None:
    # Safe to call multiple times
    load_dotenv(override=False)


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    load_env_if_present()
    return os.getenv(key, default)


def get_openai_client(explicit_api_key: Optional[str] = None) -> OpenAI:
    load_env_if_present()
    api_key = explicit_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Provide it via env or UI.")
    return OpenAI(api_key=api_key)


def configure_gemini_client(explicit_api_key: Optional[str] = None) -> None:
    # google-generativeai uses global configure
    load_env_if_present()
    api_key = explicit_api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Provide it via env or UI.")
    import google.generativeai as genai

    genai.configure(api_key=api_key)


def get_provider() -> str:
    load_env_if_present()
    provider = os.getenv("PROVIDER", "openai").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise RuntimeError(f"Unsupported PROVIDER '{provider}'. Use one of {SUPPORTED_PROVIDERS}.")
    return provider


def get_default_models(provider: Optional[str] = None) -> dict:
    load_env_if_present()
    selected = provider or get_provider()
    if selected == "openai":
        return {
            "transcription_model": os.getenv("TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
            "chat_model": os.getenv("CHAT_MODEL", "gpt-4o-mini"),
        }
    if selected == "gemini":
        return {
            "transcription_model": os.getenv("GEMINI_TRANSCRIPTION_MODEL", "gemini-1.5-flash"),
            "chat_model": os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash"),
        }
    raise RuntimeError(f"Unsupported provider '{selected}'")


