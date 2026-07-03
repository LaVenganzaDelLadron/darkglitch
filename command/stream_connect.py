# command/stream_connect.py
import os
import asyncio

if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
    # OpenCV installed in this venv only has the Qt xcb plugin,
    # so use X11 via XWayland instead of forcing native Wayland.
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2

from core.client import client_id, username
from core.config import ROOM, HOST

from signaling.peer import Peer
from signaling.signal import SignalClient






async def show_video(track, stop_event: asyncio.Event):
    frame = await track.recv()
    print("[DEBUG] Frame received:", frame.pts)
    wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    use_tk = False
    has_pil = False

    if wayland:
        try:
            import tkinter as tk
            from PIL import Image, ImageTk
            use_tk = True
            has_pil = True
        except Exception as exc:
            try:
                import tkinter as tk
                use_tk = True
                has_pil = False
            except Exception:
                print(f"[!] Tkinter unavailable for display fallback: {exc}")
                use_tk = False

    if use_tk:
        root = tk.Tk()
        root.title("GhostServer - Remote Camera")
        label = tk.Label(root)
        label.pack()
        root.update()
        print("[+] Tkinter display initialized")
    else:
        cv2.startWindowThread()
        window_name = "GhostServer - Remote Camera"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 640, 480)
        cv2.moveWindow(window_name, 100, 100)
        print("[+] OpenCV display initialized")

    frame_count = 0
    try:
        while True:
            frame = await track.recv()
            frame_count += 1
            image = frame.to_ndarray(format="bgr24")

            if use_tk:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                if has_pil:
                    img = Image.fromarray(image)
                    photo = ImageTk.PhotoImage(image=img)
                else:
                    import base64
                    h, w = image.shape[:2]
                    data = b"P6\n%d %d\n255\n" % (w, h) + image.tobytes()
                    photo = tk.PhotoImage(data=base64.b64encode(data).decode("ascii"), format="PPM")

                label.configure(image=photo)
                label.image = photo
                root.update_idletasks()
                root.update()
                if frame_count == 1:
                    print("[+] First Tkinter frame shown")
            else:
                cv2.imshow(window_name, image)
                if frame_count == 1:
                    visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                    print(f"[+] First OpenCV frame shown, window visible={visible}")
                key = cv2.waitKey(1)
                if key == 27:
                    stop_event.set()
                    break

            if stop_event.is_set():
                break

    except Exception as exc:
        print(f"[!] Video display error: {exc}")
    finally:
        if use_tk:
            try:
                root.destroy()
            except Exception:
                pass
            print("[+] Tkinter window closed")
        else:
            cv2.destroyAllWindows()
            print("[+] OpenCV window closed")


async def stream(target):
    print("[+] Connecting to stream...")

    signal = SignalClient(room=ROOM, client_id=client_id, host=HOST, username=username)
    await signal.connect()

    peer = Peer(signal)
    stop_event = asyncio.Event()

    # Request remote video/audio from the listener.
    peer.pc.addTransceiver("video", direction="recvonly")
    peer.pc.addTransceiver("audio", direction="recvonly")

    async def track_handler(track):
        print("[+] Incoming remote track, scheduling display task")
        await show_video(track, stop_event)

    peer.on_track = track_handler

    try:
        await peer.create_offer(target)
    except Exception as exc:
        print(f"[!] Failed to create offer: {exc}")
        await signal.close()
        return

    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        print("Shutdown requested")
        raise
    finally:
        print("Closing signaling connection")
        await signal.close()
