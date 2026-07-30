#!/usr/bin/env bash
# Winnie 🐕 — one-command setup & start

set -e

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║       🐕 Winnie — Browser Agent      ║"
echo "  ║       The dachshund that fetches      ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/server"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3.10+ is required. Install it first."
    exit 1
fi

# Check Python version
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PY_VERSION"

# Install deps
echo "  📦 Installing dependencies…"
pip install -r requirements.txt --quiet 2>/dev/null \
  || pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null

# Install Chromium
echo "  🌐 Ensuring Chromium is installed…"
python3 -m playwright install chromium 2>/dev/null || python3 -m playwright install chromium

echo ""
echo "  ✅ Setup complete!"
echo ""
echo "  🚀 Starting Winnie on http://127.0.0.1:8765"
echo "     Load the extension/ folder in your browser."
echo "     Press Ctrl+C to stop."
echo ""

python3 agent.py
