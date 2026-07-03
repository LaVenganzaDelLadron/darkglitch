# command/listen.py
import asyncio

import camera

from core.client import client_id, username
from core.config import ROOM, HOST
from signaling.handlers import DebugHandler
from signaling.signal import SignalClient


async def listen_mode():
    print("[+] listen mode")
    retry_delay = 600  # 10 minutes delay before retrying connection

    while True:
        signal = SignalClient(ROOM, client_id, HOST, username=username)

        try:
            await signal.connect()
            await camera.stream()

            signal.add_handler(DebugHandler())



            print(f"[+] Listening as {username} ({client_id})")

            while signal.websocket is not None and not getattr(signal.websocket, "closed", False):
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"[!] Connection failed: {exc}")

        finally:
            try:
                await signal.close()
            except Exception:
                pass

        print(f"[+] Disconnected. Reconnecting in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)
