# tools/media/receiver.py

class ReceiverUnavailableError(RuntimeError):
    """Raised when WebRTC media receiving is requested but disabled.

    The media-receiving functionality depended on `aiortc` and `cv2`
    (OpenCV), which have been removed from DarkGlitch. This module is kept
    importable so any lingering reference fails with a clear message.
    """


class Receiver:
    """WebRTC media Receiver has been removed from DarkGlitch.

    The WebRTC / OpenCV media-receiving functionality has been removed from
    the project. This class is kept as a stub that reports the feature as
    disabled rather than crashing with a `ModuleNotFoundError`.
    """

    def __init__(self, signal=None, record_file="received.mp4"):
        raise ReceiverUnavailableError(
            "WebRTC / media receiving (aiortc / OpenCV) has been disabled in "
            "DarkGlitch. This feature is no longer available."
        )
