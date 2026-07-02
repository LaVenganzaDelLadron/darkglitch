# command/listen.py
import asyncio

from core.client import client_id
from core.config import ROOM, HOST
from signaling.handlers import DebugHandler
from signaling.signal import SignalClient


async def listen_mode():
    print("[+] listen mode")

    signal = SignalClient(ROOM, client_id, HOST)
    await signal.connect()
    signal.add_handler(DebugHandler())

    print(f"[+] Listening as {client_id}")

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await signal.close()
