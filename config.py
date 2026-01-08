import os
from typing import Optional
from dotenv import load_dotenv
import google.genai as genai

SUPPORTED_PROVIDERS = ("gemini",)

def load_env_if_present() -> None:
    load_dotenv(override=False)

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    load_env_if_present()
    return os.getenv(key, default)

def configure_gemini_client(explicit_api_key: Optional[str] = None) -> None:
    load_env_if_present()
    api_key = explicit_api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Provide it via env or UI.")
    genai.configure(api_key=api_key)

def get_provider() -> str:
    load_env_if_present()
    provider = os.getenv("PROVIDER", "gemini").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise RuntimeError(f"Unsupported PROVIDER '{provider}'. Use one of {SUPPORTED_PROVIDERS}.")
    return provider

def get_default_models(provider: Optional[str] = None) -> dict:
    load_env_if_present()
    selected = provider or get_provider()
    if selected == "gemini":
        return {
            "transcription_model": os.getenv("GEMINI_TRANSCRIPTION_MODEL", "models/gemini-1.5-flash"),
            "chat_model": os.getenv("GEMINI_CHAT_MODEL", "models/gemini-1.5-flash"),
        }
    raise RuntimeError(f"Unsupported provider '{selected}'")


