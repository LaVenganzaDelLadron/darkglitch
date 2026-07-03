# command/online_list.py
import asyncio

from signaling.signal import SignalClient
from signaling.handlers import OnlineHandler
from core.config import HOST, ROOM
from core.client import client_id, username


async def online_list_mode():
    print("[+] Online list mode")

    signal = SignalClient(ROOM, client_id, HOST, username=username)

    await signal.connect()

    signal.add_handler(OnlineHandler(client_id))

    await signal.send({
        "type": "get_online"
    })

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await signal.close()