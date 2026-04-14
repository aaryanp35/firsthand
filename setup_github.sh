#!/bin/bash
# Firsthand — GitHub Setup Script
# Run this once from the firsthand/ folder on your local machine
#
# Before running:
#   1. Create an empty GitHub repo at https://github.com/new
#      Name it: firsthand
#      Leave it completely empty (no README, no .gitignore)
#   2. Run: bash setup_github.sh

set -e

echo "✦ Firsthand — GitHub Setup"
echo "──────────────────────────"

read -p "Your GitHub username: " GITHUB_USER
REPO_URL="https://github.com/${GITHUB_USER}/firsthand.git"

echo ""
echo "Setting up git..."
git init
git config user.email "aaryanp35@gmail.com"
git config user.name "Aaryan"
git branch -M main

echo "Staging files..."
git add .
git commit -m "Initial commit: Firsthand web prototype

- FastAPI backend with Gemini 2.0 Flash integration
- Two-stage pipeline: article classifier + story generator
- URL fetching and text extraction (paste link or text)
- Exponential backoff for Gemini rate limit handling
- Clean Superdesign-style UI with Inter + Lora fonts
- Vercel deployment config
- Demographic-varied persona generation across 8 US regions"

echo ""
echo "Pushing to GitHub..."
git remote add origin "$REPO_URL"
git push -u origin main

echo ""
echo "✅ Done! Repo live at: https://github.com/${GITHUB_USER}/firsthand"
echo ""
echo "Next — deploy to Vercel:"
echo "  1. Go to https://vercel.com/new"
echo "  2. Import: firsthand"
echo "  3. Add env var: GEMINI_API_KEY = your key"
echo "  4. Click Deploy"
