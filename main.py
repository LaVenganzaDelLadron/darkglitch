import asyncio
import sys


def version():
    return "1.0.0"

def help():
    print("""
    Usage:
    
    Victim:
        python main.py -l
    
    Attacker:
        python main.py -ol
        python main.py -c <client_id> <command>
    
    Options:
        -h, --help            Show help message
        -v, --version         Show version information
    
    Victim Options:
        -l, --listen          Start the client and wait for connections
    
    Attacker Options:
        -ol, --online-list    List online clients
        -c, --connect         Connect to a client
    
    Arguments:
        <client_id>           Target client ID
        <command>             Command to execute
    """)


def listen_mode():
    print("listen mode")

def online_list_mode():
    print("online list mode")

def connect_mode(target, command):
    print("connect mode")


def main():
    if len(sys.argv) < 2:
        help()
        return

    if sys.argv[1] == "-l":
        if len(sys.argv) != 3:
            help()
            return

        asyncio.run(listen_mode())

    elif sys.argv[1] == "-ol":
        if len(sys.argv) != 3:
            help()
            return

        asyncio.run(online_list_mode())

    elif sys.argv[1] == "-c":
        if len(sys.argv) != 4:
            help()
            return

        target = sys.argv[2]
        command = sys.argv[3]

        asyncio.run(connect_mode(target, command))
        
    else:
        help()

if __name__ == "__main__":
    main()
















