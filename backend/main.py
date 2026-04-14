"""
main.py — FastAPI server for Firsthand.
Serves the frontend and exposes API endpoints.

Run with:
    python main.py
Then open http://localhost:8000
"""

import os
import sys
import logging
from pathlib import Path

# Ensure backend/ is on the path so Vercel can find analyzer, generator, fetcher
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from dotenv import load_dotenv

from analyzer import classify_article
from generator import generate_story
from fetcher import fetch_article

# ── Setup ──────────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.")

logger.info("Firsthand server starting — Gemini API key loaded.")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Firsthand", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "index.html"


# ── Request models ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    text: Optional[str] = None   # Pasted article text
    url:  Optional[str] = None   # OR a URL to fetch


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if not FRONTEND_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return HTMLResponse(content=FRONTEND_PATH.read_text(encoding="utf-8"))


@app.post("/generate")
async def generate(req: GenerateRequest):
    """
    Full pipeline: get article text (from paste or URL) → classify → generate story.
    """
    # ── Resolve article text ───────────────────────────────────────────────────
    if req.url and req.url.strip():
        # URL mode — fetch and extract
        try:
            logger.info(f"Fetching article from URL: {req.url}")
            article_text = fetch_article(req.url.strip())
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    elif req.text and req.text.strip():
        # Paste mode
        article_text = req.text.strip()
        if len(article_text) < 100:
            raise HTTPException(status_code=400, detail="Article text too short — paste more content.")
        if len(article_text) > 50000:
            raise HTTPException(status_code=400, detail="Text too long — try pasting just the article body.")

    else:
        raise HTTPException(status_code=400, detail="Provide either article text or a URL.")

    # ── Pipeline ───────────────────────────────────────────────────────────────
    try:
        logger.info(f"Classifying article ({len(article_text)} chars)...")
        classification = classify_article(article_text)

        if classification.get("skip"):
            return {
                "skipped": True,
                "message": "No clear values-based divide found. Firsthand works best with opinion pieces, policy debates, or social issue reporting.",
            }

        logger.info("Generating story...")
        result = generate_story(classification)
        result["skipped"] = False
        return result

    except RuntimeError as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Something went wrong. Check the terminal for details.")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "firsthand", "model": "gemini-3.1-flash-lite-preview"}


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Firsthand at http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
