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

# Add ~/.local/bin to PATH in shell profile if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    if [[ "$SHELL" == */zsh ]]; then
        PROFILE="$HOME/.zshrc"
        echo "" >> "$PROFILE"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
    elif [[ "$SHELL" == */bash ]]; then
        # Prefer .bash_profile if it exists, otherwise .bashrc
        if [[ -f "$HOME/.bash_profile" ]]; then
            PROFILE="$HOME/.bash_profile"
        else
            PROFILE="$HOME/.bashrc"
        fi
        echo "" >> "$PROFILE"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
    elif [[ "$SHELL" == */fish ]]; then
        PROFILE="$HOME/.config/fish/config.fish"
        mkdir -p "$(dirname "$PROFILE")"
        echo "" >> "$PROFILE"
        echo 'fish_add_path $HOME/.local/bin' >> "$PROFILE"
    else
        PROFILE="$HOME/.profile"
        echo "" >> "$PROFILE"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
    fi
    echo ""
    echo "Added PATH update to $PROFILE — restart your terminal, then run: nasa"
else
    echo ""
    echo "Done. Run: nasa"
fi
