#command/list/online_list.py
import asyncio
from malware_signal.signal import SignalClient
from malware_signal.handler.online_handler import OnlineHandler
from core.data.config import HOST, ROOM
from core.data.client import client_id, username


async def online_list_mode():
    print("[+] ONLINE LIST MODE")
    signal = SignalClient(ROOM, client_id, HOST, username=username)

    await signal.connect()
    await signal.add_handler(OnlineHandler(client_id))
    await signal.send({"type": "get_online"})

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await signal.close()