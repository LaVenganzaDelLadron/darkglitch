#!/bin/bash
set -e

# Run main.py -l from the repository (script) directory
cd "$(dirname "$0")"

echo "Starting main.py -l"

# Prefer python3 when available
if command -v python3 >/dev/null 2>&1; then
	PY=python3
elif command -v python >/dev/null 2>&1; then
	PY=python
else
	echo "Error: python or python3 not found in PATH" >&2
	exit 1
fi

exec "$PY" main.py -l

