# signaling/peer.py

import asyncio
from aiortc import (
    RTCPeerConnection,
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCSessionDescription
)


class Peer:

    def __init__(self, signal):
        self.signal = signal
        self.pc = None
        self.peers = []
        self.remote_target = None
        self.on_track = None
        self.recorders = []
        self.media = None
        self.remote_candidates = []

        self._create_pc()
        signal.add_message_handler(self.handle_message)

    def _create_pc(self):
        self.pc = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        ))
        self.remote_candidates = []
        pc = self.pc

        @pc.on("iceconnectionstatechange")
        async def on_ice():
            print("[SENDER] ICE:", pc.iceConnectionState)

        @pc.on("connectionstatechange")
        async def on_conn():
            print("[WEBRTC] Connection:", pc.connectionState)

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            await self._on_icecandidate(candidate)

        @pc.on("track")
        async def on_track(track):
            print("[DEBUG] Track received:", track.kind)
            await self._on_track(track)

        if self.media is not None:
            self._add_media_tracks()

    async def _reset_pc(self):
        if self.pc is not None:
            try:
                await self.pc.close()
            except Exception:
                pass
        self._create_pc()

    def _ensure_open_pc(self):
        if self.pc is None or self.pc.signalingState == "closed" or self.pc.connectionState == "closed":
            print("[PEER] Recreating RTCPeerConnection for new session")
            self._create_pc()

    async def close(self):
        if self.pc is not None:
            try:
                await self.pc.close()
            except Exception:
                pass
            self.pc = None

    def _add_media_tracks(self):
        if self.media is None:
            return
        if self.media.video is not None:
            self.pc.addTrack(self.media.video)
        if self.media.audio is not None:
            self.pc.addTrack(self.media.audio)

    def add_media(self, media):
        self.media = media
        self._ensure_open_pc()
        self._add_media_tracks()

    async def create_offer(self, target=None):
        if target is None:
            raise TypeError("Peer.create_offer requires a target peer id")

        self.remote_target = target
        self._ensure_open_pc()

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

            if self.pc is not None and (
                self.pc.remoteDescription is not None or
                self.pc.localDescription is not None or
                self.pc.connectionState not in ("new", "closed")
            ):
                print("[PEER] Resetting RTCPeerConnection before processing new offer")
                await self._reset_pc()
            else:
                self._ensure_open_pc()

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

            while self.remote_candidates:
                candidate = self.remote_candidates.pop(0)
                await self.pc.addIceCandidate(candidate)

        elif message_type == "ice-candidate":

            candidate_data = message["data"]["candidate"]
            candidate = RTCIceCandidate(
                candidate=candidate_data["candidate"],
                sdpMid=candidate_data.get("sdpMid"),
                sdpMLineIndex=candidate_data.get("sdpMLineIndex")
            )
            if self.pc is None or self.pc.signalingState == "closed":
                print("[PEER] Dropping ICE candidate because RTCPeerConnection is closed")
                return
            if self.pc.remoteDescription is None:
                self.remote_candidates.append(candidate)
                return
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