import asyncio
import sys

import helper as h
import version as v

from command.listen import listen_mode
from command.online import online_list_mode
from command.connect import connect_mode


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

        elif sys.argv[1] == "-c":
            target = sys.argv[2]
            command = sys.argv[3]

            connect_mode(target, command)

        else:
            h.help()

    except KeyboardInterrupt:
        print("[+] Connection Closed")


if __name__ == "__main__":
    main()