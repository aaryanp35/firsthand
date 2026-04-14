# Firsthand

> Hear it firsthand from the other side.

Firsthand reads a news article and generates a short, first-person story from a fictional person on the "other side" of the issue — not through argument, through lived experience.

## Run Locally

**Prerequisites:** Python 3.10+, a [Gemini API key](https://aistudio.google.com/app/apikey) (free)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY
python main.py
```

Then open **http://localhost:8000**

## Deploy to Vercel

1. Push this repo to GitHub
2. Import the repo at [vercel.com](https://vercel.com)
3. Add environment variable: `GEMINI_API_KEY` = your key
4. Deploy — done

## How It Works

1. Paste an article URL or text
2. Gemini classifies the article's lean and the core tension
3. A fictional persona is built (name, age, location, occupation)
4. Gemini generates a ~300-word first-person story from that person's life
5. The story appears — no labels, no moral, just a person

## Project Structure

```
firsthand/
├── backend/
│   ├── main.py        # FastAPI server
│   ├── analyzer.py    # Article classification (Step 1)
│   ├── generator.py   # Story generation (Step 2)
│   ├── fetcher.py     # URL fetching and text extraction
│   ├── prompts.py     # All prompt templates — tune here
│   └── requirements.txt
├── frontend/
│   └── index.html     # Self-contained UI (no build step)
├── vercel.json
└── .gitignore
```

## Rate Limits

Free Gemini tier: 15 requests/minute, 1,500/day. The app handles rate limits automatically with exponential backoff.
