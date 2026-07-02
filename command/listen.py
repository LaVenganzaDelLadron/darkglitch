import asyncio

from core.client import username
from core.config import ROOM, HOST
from signaling.signal import SignalClient


async def listen_mode():
    print("[+] listen mode")

    signal = SignalClient(ROOM, username, HOST)

    await signal.connect()

    print(f"[+] Listening as {username}")

    while True:
        await asyncio.sleep(1)
