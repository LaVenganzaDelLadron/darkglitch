#!/usr/bin/env bash
set -euo pipefail

# Run darkglitch.py -l from the repository directory.
cd "$(dirname "$0")"

# Use python3 if available, otherwise python.
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Error: python or python3 not found in PATH" >&2
    exit 1
fi

VENV_DIR="$HOME/Desktop/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at: $VENV_DIR"
    mkdir -p "$(dirname "$VENV_DIR")"
    "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install --upgrade pip

if [ -s requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install websockets aiortc opencv-python Pillow
fi

pip install -e .

echo
echo "Virtual environment is ready at: $VENV_DIR"
echo "Activate it with: source \"$VENV_DIR/bin/activate\""

activate_line="source \"$VENV_DIR/bin/activate\""

rc_file=""
case "$(basename "${SHELL:-}")" in
    bash)
        rc_file="$HOME/.bashrc"
        ;;
    zsh)
        rc_file="$HOME/.zshrc"
        ;;
esac

if [ -z "$rc_file" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        rc_file="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        rc_file="$HOME/.zshrc"
    fi
fi

if [ -n "$rc_file" ]; then
    if ! grep -Fxq "$activate_line" "$rc_file"; then
        printf "\n###################################\n# Set always the virtual environment\n###################################\n%s\n" "$activate_line" >> "$rc_file"
        echo "Added activation line to $rc_file"
    else
        echo "Activation line already exists in $rc_file"
    fi
else
    echo "Could not detect a shell rc file. Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "$activate_line"
fi

exec "$VENV_DIR/bin/darkglitch" -l
