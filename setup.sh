#!/usr/bin/env bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Install Playwright browsers (Chromium only)
python3 -m playwright install chromium