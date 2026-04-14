"""
fetcher.py — Fetches and extracts clean article text from a URL.
Uses httpx to get the page and BeautifulSoup to extract body text.
Falls back gracefully if extraction is incomplete.
"""

import re
import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Tags most likely to contain article body content
ARTICLE_TAGS = ["article", "main", "[role=main]"]

# Tags to strip from extracted content
STRIP_TAGS = [
    "script", "style", "nav", "header", "footer",
    "aside", "figure", "figcaption", "form", "button",
    "iframe", "noscript", "svg", "img",
]

# Paywalled / blocked indicators in extracted text
PAYWALL_SIGNALS = [
    "subscribe to continue", "create a free account", "sign in to read",
    "subscriber-only", "this article is for subscribers",
    "to continue reading", "log in to read", "members only",
]


def _clean_text(raw: str) -> str:
    """Collapse whitespace and clean up extracted text."""
    # Remove excess whitespace / newlines
    text = re.sub(r"\n{3,}", "\n\n", raw)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _looks_paywalled(text: str) -> bool:
    lower = text.lower()
    return any(signal in lower for signal in PAYWALL_SIGNALS)


def fetch_article(url: str) -> str:
    """
    Fetch a URL and return clean article text.
    Raises ValueError with a user-friendly message on failure.
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info(f"Fetching URL: {url}")

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise ValueError("The article page took too long to load. Try pasting the text directly.")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            raise ValueError("This site blocked the request. Try pasting the article text directly.")
        if e.response.status_code == 404:
            raise ValueError("Article not found — double-check the URL.")
        raise ValueError(f"Could not load the page (HTTP {e.response.status_code}). Try pasting the text.")
    except Exception as e:
        raise ValueError(f"Could not fetch the URL: {str(e)[:100]}. Try pasting the text directly.")

    soup = BeautifulSoup(response.text, "lxml")

    # Strip noise
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    # Try known article containers first
    text = ""
    for selector in ARTICLE_TAGS:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(separator="\n")
            break

    # Fallback: grab all paragraphs
    if not text or len(text) < 300:
        paragraphs = soup.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs if len(p.get_text()) > 40)

    # Last resort: whole body
    if not text or len(text) < 300:
        body = soup.find("body")
        text = body.get_text(separator="\n") if body else ""

    text = _clean_text(text)

    if len(text) < 200:
        raise ValueError(
            "Couldn't extract enough text from this page. "
            "The article may be paywalled or JavaScript-rendered. "
            "Try copying and pasting the article text directly."
        )

    if _looks_paywalled(text):
        raise ValueError(
            "This article appears to be behind a paywall. "
            "Try copying and pasting the article text directly."
        )

    logger.info(f"Extracted {len(text)} chars from {url}")
    return text[:12000]  # Cap at 12k chars — more than enough for analysis
