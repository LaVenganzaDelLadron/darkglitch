# command/camera.py
import asyncio

from core.client import client_id, username
from core.config import ROOM, HOST

from signaling.peer import Peer
from media.media import LocalMedia
from signaling.signal import SignalClient


async def stream():
    print("[+] Listening as stream")

    media = LocalMedia()
    await media.start()
    print("[+] Video Track:", media.get_video_track())
    print("[+] Type Video of Track:", type(media.get_video_track()))
    print("[+] Audio Track:", media.get_audio_track())

    signal = SignalClient(
        room=ROOM,
        client_id=client_id,
        host=HOST,
        username=username,
    )

    await signal.connect()

    peer = Peer(signal)

    peer.add_media(media)

    await peer.create_offer(target="user")

    while True:
        await asyncio.sleep(1)
