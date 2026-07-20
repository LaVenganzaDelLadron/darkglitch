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

MODES::
    darkglitch -l -b                      Listen for connections (command mode)
    darkglitch -ol                        List all online connected clients
    darkglitch -b <client_id> <cmd>       Execute command on target
    darkglitch -u <client_id> <src> [dst] Upload file to target
    darkglitch -d <client_id> <src> [dst] Download file from target
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
  darkglitch -l -b

  # List all connected clients
  darkglitch -ol

  # Execute command on target client
  darkglitch -b <client_id> "whoami"

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