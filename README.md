# darkglitch

## Project Description

darkglitch is a lightweight Python project for establishing a basic signaling-backed remote command layer between peers. It provides a listener mode for clients to register with a signaling server and an attacker mode for discovering online clients and issuing remote shell commands.

The project is intended as an educational proof of concept for remote client discovery and secure command delivery over a WebSocket signaling channel.

## Features

- Listener mode to connect a client to a signaling server
- Online peer discovery to list active remote clients
- Remote command execution requests over the signaling channel
- Debug output for incoming signaling messages and peer responses
- Simple command-line interface with help and version support

## Requirements

- Python 3.10+ recommended
- `websockets` Python package

Install dependencies with:

```bash
pip install websockets
```

## Project Structure

- `main.py` - Primary entry point and command-line parser.
- `helper.py` - CLI help text and usage instructions.
- `version.py` - Version information for the project.
- `core/config.py` - Signaling server settings and room configuration.
- `core/client.py` - Client identity generation and username retrieval.
- `command/` - Command-line modes for connecting, listening, and listing online peers.
  - `connect.py` - Handles attacker mode command requests.
  - `listen.py` - Initializes a listening client that attaches to signaling.
  - `online.py` - Queries the signaling server for active peers.
- `command_injection/` - Remote command execution handler implementations.
  - `send_command.py` - Sends remote command requests and waits for results.
  - `receive_command.py` - Receives remote command requests and executes them locally.
- `signaling/` - WebSocket signaling client and message handler logic.
  - `signal.py` - Manages the signaling connection and message dispatch.
  - `handlers.py` - Message handlers for online peer listing and debug output.

## Configuration

The project uses static configuration values in `core/config.py`:

- `HOST` - Signaling server host or URL
- `ROOM` - Shared room identifier used by clients and attackers

Example values:

```python
HOST = "https://localhost:8000/"
ROOM = "test"
```

Adjust these values before launching if you need a custom signaling endpoint or room.

## Usage

Run the repository from the project root with Python.

### Show help

```bash
python main.py -h
```

### Show version

```bash
python main.py -v
```

### Start a listener (client/victim)

```bash
python main.py -l
```

### List online clients (attacker)

```bash
python main.py -ol
```

### Send a remote command to a target client

```bash
python main.py -c <client_id> "whoami"
```

Replace `<client_id>` with the target peer identifier returned by the online list mode.

## Example Output

### Listener mode

```text
[+] listen mode
[+] Listening as alice (f47ac10b-58cc-4372-a567-0e02b2c3d479)
```

### Online list mode

```text
[+] Online list mode

[+] Online peers:
  - bob (4a7d1ed4-7f75-4d1d-9e4a-93f454e8fa3e)
  - alice (f47ac10b-58cc-4372-a567-0e02b2c3d479)
[*] Your own client ID is not included in the peer list.
```

### Send command mode

```text
[+] Target : 4a7d1ed4-7f75-4d1d-9e4a-93f454e8fa3e
[+] Command: whoami
```

## Disclaimer

This repository contains functionality for remote command execution. Use it only in controlled environments and with explicit authorization. It is provided for educational and research purposes only.

Remote command execution may expose sensitive systems if used improperly. Do not deploy this code on unauthorized systems or networks.

## License

This project does not include an explicit license file. If you publish or share this repository, add a license file such as `LICENSE` to clarify usage terms.
