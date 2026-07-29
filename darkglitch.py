#darkglitch.py
import asyncio
import sys
from app.tools.command.bash import stream_mode
from app.tools.command.bash import single_bash_mode, ai_bash_mode
from app.tools.command import online_list_mode
from app.tools.command.listen.listener import listen_bash_mode, listen_stream_mode
from app.tools.command.transfer.file import upload_file, download_file
from utilities.helper import helper
from utilities.version import version


def dispatch_command(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        return "help"
    if args[0] in ("-h", "--help"):
        return "help"
    if args[0] in ("-v", "--version"):
        return "version"
    if args[0] == "-l" and len(args) >= 2 and args[1] == "-b":
        return "listen"
    if args[0] == "-ol":
        return "online_list"
    if args[0] == "-b":
        return "single_bash"
    if args[0] == "-ai":
        return "generate_command"
    if args[0] == "-u":
        return "upload_file"
    if args[0] == "-d":
        return "download_file"
    if args[0] == "-l" and len(args) >= 2 and args[1] == "-s":
        return "listen_stream"
    if args[0] == "-s":
        return "connect_stream"
    return help


def main():
    try:
        command = dispatch_command()

        if command == "help":
            helper()
            return
        if command == "version":
            print(version())
            return
        if command == "listen":
            asyncio.run(listen_bash_mode())
            return
        if command == "online_list":
            asyncio.run(online_list_mode())
            return
        if command == "single_bash":
            if len(sys.argv) < 4:
                helper()
                return
            target = str(sys.argv[2])
            command_text = sys.argv[3]
            asyncio.run(single_bash_mode(target, command_text))
            return
        if command == "generate_command":
            if len(sys.argv) < 4:
                helper()
                return
            target = str(sys.argv[2])
            command_text = sys.argv[3]
            asyncio.run(ai_bash_mode(target, command_text))
            return
        if command == "upload_file":
            if len(sys.argv) < 4:
                helper()
                return
            target = sys.argv[2]
            local_path = sys.argv[3]
            remote_path = sys.argv[4] if len(sys.argv) > 4 else None
            asyncio.run(upload_file(target, local_path, remote_path))
            return
        if command == "download_file":
            if len(sys.argv) < 4:
                helper()
                return
            target = sys.argv[2]
            remote_path = sys.argv[3]
            local_path = sys.argv[4] if len(sys.argv) > 4 else None
            asyncio.run(download_file(target, remote_path, local_path))
            return
        if command == "listen_stream":
            asyncio.run(listen_stream_mode())
            return
        if command == "connect_stream":
            if len(sys.argv) < 3:
                helper()
            target = str(sys.argv[2])
            asyncio.run(stream_mode(target))
            return
        help()

    except KeyboardInterrupt:
        print("[+] CTRL+C Detected")
        sys.exit(0)

if __name__ == "__main__":
    main()