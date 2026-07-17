# command/listen_bash.py

import asyncio

from core.client import client_id, username
from core.config import ROOM, HOST
from signaling.signal import SignalClient

from injector.command_injector import RemoteCommandHandler as ReceiverHandler


async def listen_bash_mode():
    print("[+] Listen mode")

    retry_delay = 10

    while True:
        signal = None

        try:
            # ----------------------------------
            # Signaling
            # ----------------------------------
            signal = SignalClient(room=ROOM, client_id=client_id, host=HOST, username=username)

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
            # Keep process alive until the user presses Ctrl+C
            # ----------------------------------
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("[+] Stopping listener...")
            break

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"[!] Error: {exc}")

            print(
                f"[+] Reconnecting in "
                f"{retry_delay} seconds..."
            )
            await asyncio.sleep(retry_delay)

        finally:
            print("[+] Cleaning up...")

            try:
                if signal:
                    await signal.close()
            except Exception:
                pass
