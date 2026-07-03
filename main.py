# main.py
import asyncio
import sys

import helper as h
import version as v

from command.listen import listen_mode
from command.listen_stream import listen_stream_mode
from command.online import online_list_mode
from command.bash_connect import bash_mode
from command.stream_connect import stream_mode


def dispatch_command(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        return "help"

    if args[0] in ("-h", "--help"):
        return "help"

    if args[0] in ("-v", "--version"):
        return "version"

    if args[0] == "-l" and len(args) >= 2 and args[1] == "-s":
        return "listen_stream"

    if args[0] == "-l":
        return "listen"

    if args[0] == "-ol":
        return "online_list"

    if args[0] == "-s":
        return "stream"

    if args[0] == "-c":
        return "bash"

    return "help"


def main():
    try:
        command = dispatch_command()

        if command == "help":
            h.help()
            return

        if command == "version":
            print(v.version())
            return

        if command == "listen":
            asyncio.run(listen_mode())
            return

        if command == "listen_stream":
            asyncio.run(listen_stream_mode())
            return

        if command == "online_list":
            asyncio.run(online_list_mode())
            return

        if command == "stream":
            if len(sys.argv) < 3:
                h.help()
                return
            target = str(sys.argv[2])
            asyncio.run(stream_mode(target))
            return

        if command == "bash":
            if len(sys.argv) < 4:
                h.help()
                return
            target = sys.argv[2]
            command_text = sys.argv[3]
            asyncio.run(bash_mode(target, command_text))
            return

        h.help()

    except KeyboardInterrupt:
        print("[+] Connection Closed")


if __name__ == "__main__":
    main()