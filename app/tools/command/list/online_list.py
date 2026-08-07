#command/list/online_list.py
import asyncio
from app.malware_signal.signal import SignalClient
from app.malware_signal.handler.online_handler import OnlineHandler
from app.core.data.config import HOST, ROOM
from app.core.data.client import client_id, username


async def online_list_mode():
    print("[+] ONLINE LIST MODE")
    signal = SignalClient(ROOM, client_id, HOST, username=username)

    try:
        signal.add_handler(OnlineHandler(client_id))
        await signal.connect()
        await signal.send({"type": "get_online"})
        await signal.listen()
    except asyncio.CancelledError:
        pass
    finally:
        await signal.close()
