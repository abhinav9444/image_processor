#!/usr/bin/env bash
set -e

echo "=============================================="
echo " E-Commerce Image Processor - Linux/macOS"
echo "=============================================="

PYTHON_CMD=""

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "Python 3 is required. Install Python 3.10+ and run this script again."
    exit 1
fi

"$PYTHON_CMD" -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"' || {
    echo "Python 3.10+ is required."
    exit 1
}

echo "[1/3] Creating virtual environment..."
"$PYTHON_CMD" -m venv .venv

echo "[2/3] Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[3/3] Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "Installation complete."
echo
echo "Activate later with:"
echo "  source .venv/bin/activate"
echo
echo "Then run:"
echo "  python image_processor.py --list-resolutions"
echo "  python image_processor.py input --output output"
