import os
import cv2
import asyncio

async def show_video(track, stop_event: asyncio.Event):
    wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    use_tk = False
    tk = None
    Image = None
    ImageTk = None

    if wayland:
        try:
            import tkinter as tk
            from PIL import Image, ImageTk
            use_tk = True
        except Exception as exc:
            print(f"[!] TKINTER/PILLOW NOT AVAILABLE FOR DISPLAY FALLBACK: {exc}")
            use_tk = False

    window_name = "GhostServer - Remote Camera"

    if use_tk:
        root = tk.Tk()
        root.title(window_name)
        label = tk.Label(root)
        label.pack()
        root.update()
        print("[+] TKINTER DISPLAY INITIALIZED")
    else:
        cv2.startWindowThread()
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 640, 480)
        cv2.moveWindow(window_name, 100, 100)
        print("[+] OPENCV DISPLAY INITIALIZED")

    frame_count = 0
    first_frame_logged = False
    try:
        while True:
            try:
                frame = await track.recv()
            except Exception as exc:
                print(f"[!] FAILED TO RECEIVE VIDEO FRAME: {exc}")
                import traceback
                print(traceback.format_exc())
                await asyncio.sleep(0.1)
                continue

            frame_count += 1
            if not first_frame_logged:
                print(
                    f"[DEBUG] FRAME #{frame_count} type={type(frame).__name__} "
                    f"pts={getattr(frame, 'pts', None)} dts={getattr(frame, 'dts', None)}"
                )

            try:
                image = frame.to_ndarray(format="bgr24")
                if not first_frame_logged:
                    print(f"[DEBUG] NDARRAY shape={image.shape} dtype={image.dtype}")
            except Exception as exc:
                print(f"[!] FAILED TO CONVERT VIDEOFRAME TO NDARRAY: {exc}")
                import traceback
                print(traceback.format_exc())
                continue

            if use_tk:
                try:
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb)
                    photo = ImageTk.PhotoImage(image=img)
                    if not first_frame_logged:
                        print(
                            f"[DEBUG] PIL image type={type(img).__name__} "
                            f"PhotoImage type={type(photo).__name__}"
                        )

                    label.configure(image=photo)
                    label.image = photo
                    root.update_idletasks()
                    root.update()
                    if frame_count == 1:
                        print("[+] First Tkinter frame shown")
                except Exception as exc:
                    print(f"[!] Tkinter display error on frame #{frame_count}: {exc}")
                    import traceback
                    print(traceback.format_exc())
                    continue
            else:
                try:
                    cv2.imshow(window_name, image)
                    if frame_count == 1:
                        visible = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                        print(f"[+] FIRST OPENCV FRAME SHOWN, WINDOW visible={visible}")
                    key = cv2.waitKey(1)
                    if key == 27:
                        stop_event.set()
                        break
                except Exception as exc:
                    print(f"[!] OPENCV DISPLAY ERROR ON FRAME #{frame_count}: {exc}")
                    import traceback
                    print(traceback.format_exc())
                    continue

            if not first_frame_logged:
                first_frame_logged = True

            if stop_event.is_set():
                break

    except Exception as exc:
        print(f"[!] VIDEO DISPLAY LOOP FATAL ERROR: {exc}")
        import traceback
        print(traceback.format_exc())
    finally:
        if use_tk:
            try:
                root.destroy()
            except Exception:
                pass
            print("[+] TKINTER WINDOW CLOSED")
        else:
            cv2.destroyAllWindows()
            print("[+] OPENCV WINDOW CLOSED")