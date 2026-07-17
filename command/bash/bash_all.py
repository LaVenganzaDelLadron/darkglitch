# command/bash/bash_all.py
from asyncio import timeout
from unittest import result

from signaling.signal import SignalClient
from signaling.handlers import OnlineHandler
from core.config import HOST, ROOM
from core.client import client_id, username
from injector.command_injector import RemoteCommandHandler as SenderHandler

async def bash_mode_all(command):
    print("[+] Bash Mode All")

    signal = SignalClient(ROOM, client_id, HOST, username=username)

    await signal.connect()

    sender = SenderHandler(signal)

    """signal.add_handler(OnlineHandler(client_id))

    await signal.send({
        "type": "get_online"
    })"""

    try:
        result = await sender.send_command(
            target="client_id",
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
