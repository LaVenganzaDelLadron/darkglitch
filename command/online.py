import asyncio

from signaling.signal import SignalClient
from signaling.handlers import online_handler
from core.config import HOST, ROOM
from core.client import username


async def online_list_mode():
    print("[+] Online list mode")

    signal = SignalClient(ROOM, username, HOST)

    await signal.connect()

    signal.add_handler(online_handler)

    await signal.send({
        "type": "get_online"
    })

    await asyncio.sleep(5)

    await signal.close()