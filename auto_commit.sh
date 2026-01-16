#!/bin/bash

# auto_commit.sh
# Automates adding all files, committing with a timestamp, and pushing to main.

echo "🦅 Staging all changes..."
git add .

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "🗽 Committing with timestamp: $TIMESTAMP"
git commit -m "Holdings update: $TIMESTAMP"

echo "🚀 Pushing to origin/main..."
git branch -M main
git push -u origin main

echo "✅ Done!"
