"""
analyzer.py — Step 1 of the pipeline.
Takes raw article text, returns a structured classification object.
Handles Gemini rate limits with exponential backoff.
"""

import json
import time
import logging
import re
import os

import google.generativeai as genai
from prompts import CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)

MAX_RETRIES = 8
BASE_WAIT_SECONDS = 15
MAX_WAIT_SECONDS = 3600


def _get_model() -> genai.GenerativeModel:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
    return model


def _wait_for_reset(attempt: int) -> None:
    wait = min(BASE_WAIT_SECONDS * (2 ** attempt), MAX_WAIT_SECONDS)
    logger.warning(f"Rate limited. Waiting {wait}s before retry (attempt {attempt + 1}/{MAX_RETRIES})")
    time.sleep(wait)


def _clean_json_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def classify_article(article_text: str) -> dict:
    """
    Send article text to Gemini and get a structured classification back.
    Returns a dict matching the CLASSIFIER_PROMPT schema.
    Raises RuntimeError if all retries are exhausted.
    """
    model = _get_model()
    prompt = CLASSIFIER_PROMPT.format(article_text=article_text[:8000])

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 512,
                },
            )
            raw = response.text
            cleaned = _clean_json_response(raw)
            data = json.loads(cleaned)

            required_keys = ["topic", "article_lean", "core_tension", "other_side_profile", "skip"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Missing key in classification response: {key}")

            logger.info(f"Classified: topic='{data['topic']}' lean='{data['article_lean']}' skip={data['skip']}")
            return data

        except Exception as e:
            error_str = str(e).lower()

            if any(p in error_str for p in ["429", "quota", "resource exhausted", "rate limit"]):
                if attempt < MAX_RETRIES - 1:
                    _wait_for_reset(attempt)
                    continue
                raise RuntimeError("Gemini rate limit — all retries exhausted. Try again after quota resets.") from e

            if isinstance(e, (json.JSONDecodeError, ValueError)) and attempt < 2:
                logger.warning(f"Failed to parse classification JSON (attempt {attempt + 1}): {e}. Retrying...")
                time.sleep(2)
                continue

            logger.error(f"Unexpected error during classification: {e}")
            raise RuntimeError(f"Classification failed: {e}") from e

    raise RuntimeError("Max retries exceeded during article classification.")
