#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-git@github.com:bilgi-ship-it/kepenk.git}"

if [[ -d .git ]]; then
  echo "A Git repository already exists here." >&2
  exit 1
fi

git init
git add .
git commit -m "feat: initialize Kepenk agent safety gate"
git branch -M main
git remote add origin "$REPO_URL"
git push -u origin main
