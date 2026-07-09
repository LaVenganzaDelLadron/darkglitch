# command/bash/bash_connect.py
import asyncio

from signaling.signal import SignalClient
from core.config import HOST, ROOM
from core.client import client_id, username

from command_injection.injector import RemoteCommandHandler as SenderHandler

async def bash_mode(target, command):
    print("[+] Bash Mode")

    signal = SignalClient(ROOM, client_id, HOST, username=username)
    await signal.connect()

    sender = SenderHandler(signal)

    try:
        result = await sender.send_command(
            target=target,
            command=command,
            wait_for_result=True,
            timeout=15,
        )

        if result is None:
            print("[-] No response received for remote command")
            return

        if result.get("status") == "success":
            print(result.get("output", "Bash executed successfully"))
        else:
            print("[-] Bash Failed")
            print("ERROR:", result.get("error", "Unknown error"))
    finally:
        await signal.close()
