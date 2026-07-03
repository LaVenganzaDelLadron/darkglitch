# main.py
import asyncio
import sys

import helper as h
import version as v

from command.listen import listen_mode
from command.online import online_list_mode
from command.bash_connect import bash_mode
from command.stream_connect import stream_mode

def main():
    try:
        if len(sys.argv) < 2:
            h.help()
            return

        if sys.argv[1] in ("-h", "--help"):
            h.help()

        elif sys.argv[1] in ("-v", "--version"):
            print(v.version())

        elif sys.argv[1] == "-l":
            asyncio.run(listen_mode())

        elif sys.argv[1] == "-ol":
            asyncio.run(online_list_mode())

        elif sys.argv[1] == "-s":
            if len(sys.argv) < 3:
                h.help()
                return
            target = str(sys.argv[2])
            asyncio.run(stream_mode(target))

        elif sys.argv[1] == "-c":
            if len(sys.argv) < 4:
                h.help()
                return
            target = sys.argv[2]
            command = sys.argv[3]

            asyncio.run(bash_mode(target, command))

        else:
            h.help()

    except KeyboardInterrupt:
        print("[+] Connection Closed")


if __name__ == "__main__":
    main()