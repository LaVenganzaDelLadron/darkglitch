# command/stream_connect.py
import argparse
import asyncio

from core.client import client_id, username
from core.config import ROOM, HOST

from signaling.signal import SignalClient






async def stream(target):
    print("[+] Connecting to stream...")

    signal = SignalClient(room=ROOM, client_id=client_id, host=HOST, username=username)
    try:

        await signal.connect()

        signal.add_handler()

    except InterruptedError:
        print("[-] Streaming is interrupted")

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        print("Shutdown requested")
        raise
    finally:
        print("Closing signaling connection")
        await signal.close()
