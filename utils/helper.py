from utils import banner

def help():

    banner.randomizer()
    print("""Usage:
    Victim:
        darkglitch -l -c
        darkglitch -l -s
    Attacker:
        darkglitch -ol
        darkglitch -s <client_id>
        darkglitch -c <client_id> <command_injection>
        darkglitch -u <client_id> <local_path> [remote_path]
        darkglitch -d <client_id> <remote_path> [local_path]
    Options:
        -h, --help            Show help message
        -v, --version         Show version information
    Victim Options:
        -l, --listen          Start the client and wait for connections
        -s, --stream          Stream a webcam the client and wait for connections  
    Attacker Options:
        -ol, --online-list    List online clients
        -c, --connect         Connect to a client
        -u, --upload          Upload a file or folder to the target client
        -d, --download        Download a file or folder from the target client
    Arguments:
        <client_id>           Target client ID
        <command_injection>   Command to execute
        <local_path>          Local path of the file
        <remote_path>         Remote path of the file
    """)