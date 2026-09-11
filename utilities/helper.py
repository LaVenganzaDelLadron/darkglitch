from utilities import banner, version

def helper():

    banner.randomizer()
    print(f"""
Darkglitch {version.version()} ( https://github.com/LaVenganzaDelLadron/darkglitch.git )
Advanced Command & Control Framework for Remote System Management

DESCRIPTION:
  Darkglitch is a powerful post-exploitation framework designed for remote
  command execution and file transfer. It operates in a client-server
  architecture with secure communication over WebSocket signaling.

USAGE:
  darkglitch [MODE] [OPTIONS] [ARGUMENTS]

MODES::
    darkglitch -l -b                      Listen for connections (command mode)
    darkglitch -ol                        List all online connected clients
    darkglitch -b <client_id> <cmd>       Execute command on target
    darkglitch -u <client_id> <src> [dst] Upload file to target
    darkglitch -d <client_id> <src> [dst] Download file from target
    darkglitch -ai <client_id> <prompt>   Using Prompt to execute command
    darkglitch persistence [options]     Detect OS persistence mechanisms
    darkglitch privileges [options]      Audit privileged accounts and groups
    darkglitch credentials [paths]       Scan text files for exposed credentials
    darkglitch -s <client_id>
    darkglitch -ai-unsafe <client_id> <prompt>   Using Prompt to execute command

GENERAL OPTIONS:
  -h, --help                              Display this help message
  -v, --version                           Display version information

PERSISTENCE OPTIONS:
  --baseline <path>                       Compare against a JSON baseline
  --save-baseline                        Save the current entries as baseline
  --json                                 Emit a machine-readable report
  --watch [seconds]                      Repeat read-only scans (default: 60)

PRIVILEGE OPTIONS:
  --baseline <path>                      Compare against a JSON baseline
  --save-baseline                        Save the current privileged identities
  --json                                 Emit a machine-readable report

CREDENTIAL OPTIONS:
  [paths]                                Files or directories (default: current directory)
  --json                                 Emit a machine-readable report with redacted values

ARGUMENTS:
  <client_id>                             Target client identifier
  <command>                               Shell command to execute
  <src>, <source>                         Source file or directory path
  [dst], [destination]                    Destination path (optional)
EXAMPLES:
  # Start a client listener
  darkglitch -l -b

  # List all connected clients
  darkglitch -ol

  # Execute command on target client
  darkglitch -b <client_id> "whoami"

  # Upload local file to target
  darkglitch -u <client_id> <src> [dst]

  # Download file from target
  darkglitch -d <client_id> <src> [dst]

  # AI
  darkglitch -ai <client_id> "what is the feature of this computer"
  darkglitch -ai-unsafe <client_id> "give me a command that can delete system32"

COMING SOON:
  -rc, --reverse-shell                    Establish reverse shell connection
  -ex, --exfiltrate                       Data exfiltration capabilities

SEE ALSO:
  GitHub: https://github.com/LaVenganzaDelLadron/
  Documentation: Check README.md for detailed usage guides
    """)