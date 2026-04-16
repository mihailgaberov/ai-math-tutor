#!/usr/bin/env bash
set -e

MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"

echo "🧮 Starting AI Math Tutor..."

# ── 1. Ensure Ollama is installed ─────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    echo "📦 Ollama not found. Installing via Homebrew..."
    brew install ollama
fi

# ── 2. Start Ollama server if not running ─────────────────────────────────────
if ! curl -s http://localhost:11434 &>/dev/null; then
    echo "🚀 Starting Ollama server..."
    ollama serve &
    sleep 3
fi

# ── 3. Pull model if not present ──────────────────────────────────────────────
if ! ollama list | grep -q "$MODEL"; then
    echo "⬇️  Pulling model $MODEL (one-time download ~2 GB)..."
    ollama pull "$MODEL"
fi

# ── 4. Set up virtual environment and install dependencies ───────────────────
if [ ! -d .venv ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

if ! .venv/bin/python -c "import streamlit" &>/dev/null; then
    echo "📦 Installing Python dependencies..."
    .venv/bin/pip install streamlit ollama python-dotenv
fi

# ── 5. Copy .env if not present ───────────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

# ── 6. Launch app ─────────────────────────────────────────────────────────────
echo "✅ All good! Opening Maximo in your browser..."
.venv/bin/streamlit run app.py --server.headless false
