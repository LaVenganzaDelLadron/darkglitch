import asyncio
import sys
import helper as h
import version as v

def listen_mode():
    print("listen mode")

def online_list_mode():
    print("online list mode")

def connect_mode(target, command):
    print("connect mode")


def main():
    if len(sys.argv) < 2:
        h.help()
        return

    if sys.argv[1] in ("-h", "--help"):
        h.help()

    elif sys.argv[1] in ("-v", "--version"):
        print(v.version())

    elif sys.argv[1] == "-l":
        if len(sys.argv) != 2:
            h.help()
            return
        listen_mode()

    elif sys.argv[1] == "-ol":
        if len(sys.argv) != 2:
            h.help()
            return
        online_list_mode()

    elif sys.argv[1] == "-c":
        if len(sys.argv) != 4:
            h.help()
            return

        target = sys.argv[2]
        command = sys.argv[3]
        connect_mode(target, command)

    else:
        h.help()

if __name__ == "__main__":
    main()
















