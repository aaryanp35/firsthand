"""
generator.py — Step 2 of the pipeline.
Takes a classification dict, builds a fictional persona, generates the story.
"""

import time
import random
import logging
import re
import os

from google import genai
from google.genai import types
from prompts import (
    STORY_PROMPT,
    NAMES_BY_REGION,
    AGES_BY_LIFE_STAGE,
    LOCATIONS_BY_REGION,
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 8
BASE_WAIT_SECONDS = 15
MAX_WAIT_SECONDS = 3600

_recent_personas: list[dict] = []
MAX_PERSONA_HISTORY = 10


def _get_client() -> genai.Client:
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _wait_for_reset(attempt: int) -> None:
    wait = min(BASE_WAIT_SECONDS * (2 ** attempt), MAX_WAIT_SECONDS)
    logger.warning(f"Rate limited. Waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
    time.sleep(wait)


def _pick_name(region: str, used_names: list[str]) -> str:
    region_names = NAMES_BY_REGION.get(region, NAMES_BY_REGION["suburban Midwest"])
    gender = random.choice(["male", "female"])
    candidates = [n for n in region_names[gender] if n not in used_names]
    if not candidates:
        candidates = region_names[gender]
    return random.choice(candidates)


def _pick_age(life_stage: str) -> int:
    lo, hi = AGES_BY_LIFE_STAGE.get(life_stage, (35, 55))
    return random.randint(lo, hi)


def _pick_location(region: str) -> str:
    locations = LOCATIONS_BY_REGION.get(region, ["Springfield, USA"])
    return random.choice(locations)


def _build_persona(classification: dict) -> dict:
    profile = classification["other_side_profile"]
    region = profile.get("region", "suburban Midwest")
    life_stage = profile.get("life_stage", "middle-aged parent (40s)")
    occupation = profile.get("occupation", "factory worker")
    anchor_theme = profile.get("anchor_theme", "")

    recent_regions = [p["region"] for p in _recent_personas[-3:]]
    if region in recent_regions:
        similar = {
            "rural South": "rural Midwest",
            "rural Midwest": "rural South",
            "suburban South": "suburban Midwest",
            "suburban Midwest": "suburban South",
        }
        region = similar.get(region, region)

    used_names = [p.get("name", "") for p in _recent_personas]
    name = _pick_name(region, used_names)
    age = _pick_age(life_stage)
    location = _pick_location(region)

    persona = {
        "name": name,
        "age": age,
        "location": location,
        "occupation": occupation,
        "anchor_theme": anchor_theme,
        "region": region,
    }

    _recent_personas.append(persona)
    if len(_recent_personas) > MAX_PERSONA_HISTORY:
        _recent_personas.pop(0)

    return persona


def _clean_story(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^(?:Here(?:'s| is)(?: the)? story:?|Story:|---)\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _word_count(text: str) -> int:
    return len(text.split())


def generate_story(classification: dict) -> dict:
    """
    Generate a first-person story from the classification.
    Returns story text, persona info, and metadata.
    """
    persona = _build_persona(classification)
    tension = classification["core_tension"]
    article_lean = classification.get("article_lean", "neutral")

    prompt = STORY_PROMPT.format(
        name=persona["name"],
        age=persona["age"],
        location=persona["location"],
        occupation=persona["occupation"],
        anchor_theme=persona["anchor_theme"],
        topic=classification["topic"],
        article_lean=article_lean,
        other_side_value=tension.get("other_side_value", ""),
    )

    client = _get_client()

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="models/gemini-3.1-flash-lite-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    max_output_tokens=700,
                ),
            )
            story_text = _clean_story(response.text)
            wc = _word_count(story_text)
            logger.info(f"Generated story: {persona['name']}, {persona['location']} ({wc} words)")

            if wc < 150:
                logger.warning(f"Story too short ({wc} words), retrying...")
                time.sleep(3)
                continue

            return {
                "story": story_text,
                "persona": {
                    "name": persona["name"],
                    "age": persona["age"],
                    "location": persona["location"],
                    "occupation": persona["occupation"],
                },
                "meta": {
                    "topic": classification["topic"],
                    "article_lean": article_lean,
                    "other_side_value": tension.get("other_side_value", ""),
                    "word_count": wc,
                },
            }

        except Exception as e:
            error_str = str(e).lower()
            if any(p in error_str for p in ["429", "quota", "resource exhausted", "rate limit"]):
                if attempt < MAX_RETRIES - 1:
                    _wait_for_reset(attempt)
                    continue
                raise RuntimeError("Gemini rate limit — all retries exhausted.") from e

            logger.error(f"Story generation error: {e}")
            raise RuntimeError(f"Story generation failed: {e}") from e

    raise RuntimeError("Max retries exceeded during story generation.")
