import os
import random
import time

from google import genai

PRIMARY_MODEL = "models/gemini-3.1-flash-lite-preview"
FALLBACK_MODEL = "models/gemini-2.5-flash"
EMERGENCY_MODEL = "models/gemini-2.5-flash-lite"
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0


def _is_503_unavailable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "503" in msg and "unavailable" in msg


def _generate_once(client: genai.Client, model_name: str, prompt: str) -> str:
    print(f"Using model: {model_name}")
    response = client.models.generate_content(model=model_name, contents=prompt)
    return (response.text or "").strip()


def _call_with_retry_for_503(client: genai.Client, model_name: str, prompt: str) -> str:
    for attempt in range(MAX_RETRIES + 1):
        try:
            return _generate_once(client, model_name, prompt)
        except Exception as exc:
            if not _is_503_unavailable(exc):
                raise
            if attempt >= MAX_RETRIES:
                raise
            delay = (BASE_DELAY_SECONDS * (2 ** attempt)) + random.uniform(0, 0.5)
            print(f"503 UNAVAILABLE from {model_name}. Retrying in {delay:.2f}s...")
            time.sleep(delay)

    raise RuntimeError("Unexpected retry loop exit")


def call_gemini(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be a non-empty string")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    try:
        return _call_with_retry_for_503(client, PRIMARY_MODEL, prompt)
    except Exception as primary_err:
        print(f"Primary model failed: {primary_err}")

    try:
        return _generate_once(client, FALLBACK_MODEL, prompt)
    except Exception as fallback_err:
        print(f"Fallback model failed: {fallback_err}")

    try:
        return _generate_once(client, EMERGENCY_MODEL, prompt)
    except Exception as emergency_err:
        raise RuntimeError(
            "All model attempts failed "
            f"(primary={PRIMARY_MODEL}, fallback={FALLBACK_MODEL}, emergency={EMERGENCY_MODEL})"
        ) from emergency_err


if __name__ == "__main__":
    try:
        sample_prompt = "Summarize why resilient API clients use retries and fallbacks in 3 bullets."
        output = call_gemini(sample_prompt)
        print("\nResponse:\n")
        print(output)
    except Exception as exc:
        print(f"Error: {exc}")
