#!/usr/bin/env bash
set -e
source .venv/bin/activate
python image_processor.py "$@"
