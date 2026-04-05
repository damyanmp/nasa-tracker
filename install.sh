#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/damyanmp/nasa-tracker"

# Install uv if not present
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing nasa-tracker..."
uv tool install "git+$REPO" --force

# Warn if ~/.local/bin is not in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "NOTE: Add this to your shell profile (~/.zshrc or ~/.bash_profile):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then restart your terminal and run: nasa"
else
    echo ""
    echo "Done. Run: nasa"
fi
