# darkglitch.py
import asyncio
import sys

from command.upload_file import upload_file
from command.upload_file import upload_file, download_file
from utils.helper import help
from utils.version import version

from command.listen_bash import listen_bash_mode
from command.listen_stream import listen_stream_mode
from command.online_list import online_list_mode
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

    if args[0] == "-l" and len(args) >= 2 and args[1] == "-c":
        return "listen"

    if args[0] == "-u":
        return "upload_file"

    if args[0] == "-d":
        return "download_file"

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
            help()
            return

        if command == "version":
            print(version())
            return

        if command == "listen":
            asyncio.run(listen_bash_mode())
            return

        if command == "listen_stream":
            asyncio.run(listen_stream_mode())
            return

        if command == "online_list":
            asyncio.run(online_list_mode())
            return

        if command == "stream":
            if len(sys.argv) < 3:
                help()
                return
            target = str(sys.argv[2])
            asyncio.run(stream_mode(target))
            return

        if command == "bash":
            if len(sys.argv) < 4:
                help()
                return
            target = sys.argv[2]
            command_text = sys.argv[3]
            asyncio.run(bash_mode(target, command_text))
            return

        if command == "upload_file":
            if len(sys.argv) < 4:
                help()
                return
            target = sys.argv[2]
            local_path = sys.argv[3]
            remote_path = sys.argv[4] if len(sys.argv) > 4 else None
            asyncio.run(upload_file(target, local_path, remote_path))
            return

        if command == "download_file":
            if len(sys.argv) < 4:
                help()
                return
            target = sys.argv[2]
            remote_path = sys.argv[3]
            local_path = sys.argv[4] if len(sys.argv) > 4 else None
            asyncio.run(download_file(target, remote_path, local_path))
            return

        help()

    except KeyboardInterrupt:
        print("[+] Connection Closed")


if __name__ == "__main__":
    main()