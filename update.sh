#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/damyanmp/nasa-tracker"

if ! command -v uv &>/dev/null; then
    echo "uv not found — is nasa-tracker installed? Run the install script first:"
    echo "  curl -fsSL https://raw.githubusercontent.com/damyanmp/nasa-tracker/main/install.sh | bash"
    exit 1
fi

echo "Updating uv..."
uv self update || echo "(skipping uv self-update — uv was installed by a package manager)"

echo "Updating nasa-tracker..."
# --reinstall forces a fresh fetch from GitHub even if the version number didn't change
uv tool install --force --reinstall "git+$REPO"

echo ""
echo "Done. Run: nasa version"
