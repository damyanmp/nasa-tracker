#!/usr/bin/env bash
set -euo pipefail

# Ensure uv is available
if ! command -v uv &>/dev/null; then
    echo "uv not found — is nasa-tracker installed? Run the install script first:"
    echo "  curl -fsSL https://raw.githubusercontent.com/damyanmp/nasa-tracker/main/install.sh | sh"
    exit 1
fi

echo "Updating uv..."
uv self update

echo "Updating nasa-tracker..."
uv tool upgrade nasa-tracker

echo ""
echo "Done. Run: nasa"
