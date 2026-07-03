# signaling/peer.py
import asyncio

from aiortc import (
    RTCPeerConnection,
    RTCIceCandidate,
    RTCSessionDescription
)


class Peer:

    def __init__(self, signal):
        self.signal = signal
        self.pc = RTCPeerConnection()
        self.peers = []
        self.remote_target = None
        self.on_track = None
        self.recorders = []

        signal.add_message_handler(self.handle_message)

        @self.pc.on("iceconnectionstatechange")
        async def on_ice():
            print("[SENDER] ICE:", self.pc.iceConnectionState)

        @self.pc.on("connectionstatechange")
        async def on_conn():
            print("[WEBRTC] Connection:", self.pc.connectionState)

        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            await self._on_icecandidate(candidate)

        @self.pc.on("track")
        async def on_track(track):
            print("[DEBUG] Track received:", track.kind)
            await self._on_track(track)

    def add_media(self, media):

        if media.video is not None:
            self.pc.addTrack(media.video)
        if media.audio is not None:
            self.pc.addTrack(media.audio)

    async def create_offer(self, target=None):
        if target is None:
            raise TypeError("Peer.create_offer requires a target peer id")

        self.remote_target = target

        offer = await self.pc.createOffer()

        await self.pc.setLocalDescription(offer)

        await self.signal.send({
            "type": "offer",
            "target": target,
            "data": {
                "sdp": self.pc.localDescription.sdp,
                "type": self.pc.localDescription.type
            }
        })

    async def _on_icecandidate(self, candidate):
        if candidate is None or self.remote_target is None:
            return

        await self.signal.send({
            "type": "ice-candidate",
            "target": self.remote_target,
            "data": {
                "candidate": {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                }
            }
        })

    async def _on_track(self, track):
        print("Received remote track:", track.kind)

        if self.on_track is not None:
            print("[+] Scheduling on_track handler")
            asyncio.create_task(self.on_track(track))
            return

        print("[!] No on_track handler registered")
        from aiortc.contrib.media import MediaBlackhole

        blackhole = MediaBlackhole()
        blackhole.addTrack(track)
        self.recorders.append(blackhole)
        await blackhole.start()

    async def handle_message(self, message):
        message_type = message.get("type")

        if message_type == "offer":
            self.remote_target = message.get("sender")
            desc = RTCSessionDescription(
                sdp=message["data"]["sdp"],
                type=message["data"]["type"],
            )

            await self.pc.setRemoteDescription(desc)

            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)

            await self.signal.send({
                "type": "answer",
                "target": self.remote_target,
                "data": {
                    "sdp": self.pc.localDescription.sdp,
                    "type": self.pc.localDescription.type,
                },
            })

        elif message_type == "ice-candidate":

            candidate_data = message["data"]["candidate"]
            candidate = RTCIceCandidate(
                candidate=candidate_data["candidate"],
                sdpMid=candidate_data.get("sdpMid"),
                sdpMLineIndex=candidate_data.get("sdpMLineIndex")
            )
            await self.pc.addIceCandidate(candidate)

        elif message_type == "peer-list":
            self.peers = message["data"].get("peers", [])
            print("Peer list:", self.peers)

        elif message_type == "answer":
            desc = RTCSessionDescription(
                sdp=message["data"]["sdp"],
                type=message["data"]["type"],
            )

            await self.pc.setRemoteDescription(desc)