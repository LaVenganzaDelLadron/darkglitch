# darkglitch

## Project Description

darkglitch is a small Python proof-of-concept for remote command delivery over a WebSocket signaling channel. It supports a listener mode to register a client and an attacker mode to find online peers and send remote shell commands.

## Important Notes

- This project is educational only.
- Use it only in authorized test environments.
- Remote command execution can be dangerous if misused.

## Requirements

- Python 3.10+
- `requirements.txt` is provided for dependency installation

## Setup

From the project root:

```bash
./install.sh
```

This script will:

- create a Python virtual environment at `~/Desktop/venv`
- activate that environment
- install dependencies from `requirements.txt`
- add `source ~/Desktop/venv/bin/activate` to your `~/.bashrc` or `~/.zshrc`
- start the listener mode with `main.py -l`

If you prefer manual setup:

```bash
python3 -m venv ~/Desktop/venv
source ~/Desktop/venv/bin/activate
pip install -r requirements.txt
```

## Dependencies

- `websockets`
- `aiortc`
- `opencv-python`
- `Pillow`

## Project Structure

- `main.py` - Entry point and command parser
- `helper.py` - CLI help text
- `version.py` - Version information
- `core/config.py` - Signaling server settings
- `core/client.py` - Client identity and username logic
- `command/`
  - `bash_connect.py` - Send remote commands
  - `listen.py` - Start listener mode
  - `online.py` - List online peers
  - `stream_connect.py` - Request remote media stream
- `command_injection/injector.py` - Remote command request handling
- `signaling/`
  - `signal.py` - WebSocket signaling client
  - `peer.py` - WebRTC peer connection logic
- `media/`
  - `local_media.py` - Local camera/microphone handling
  - `receiver_media.py` - Remote media receiver

## Configuration

Edit `core/config.py` to set:

- `HOST` - signaling server URL
- `ROOM` - shared room identifier

Example:

```python
HOST = "https://localhost:8000/"
ROOM = "test"
```

## Usage

### Show help

```bash
python darkglitch.py -h
```

### Show version

```bash
python darkglitch.py -v
```

### Start listener mode

```bash
python darkglitch.py -l
```

### List online peers

```bash
python darkglitch.py -ol
```

### Send a remote command

```bash
python darkglitch.py -c <client_id> "whoami"
```

Replace `<client_id>` with the target identifier from the online peers list.

## Disclaimer

This repository is for research and learning only. Do not deploy it against systems or networks without explicit permission.
