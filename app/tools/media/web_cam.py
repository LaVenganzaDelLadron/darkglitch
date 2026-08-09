# tools/media/web_cam.py

class WebCamUnavailableError(RuntimeError):
    """Raised when webcam capture is requested but disabled.

    The webcam capture functionality depended on `aiortc`, which has been
    removed from DarkGlitch. This module is kept importable so any lingering
    reference fails with a clear message.
    """


class WebCam:
    """WebCam capture has been removed from DarkGlitch.

    The webcam / media-capture functionality depended on the `aiortc` library,
    which has been removed from the project. This class is kept as a stub that
    reports the feature as disabled rather than crashing with a
    `ModuleNotFoundError`.
    """

    def __init__(self):
        raise WebCamUnavailableError(
            "Webcam capture (aiortc) has been disabled in DarkGlitch. "
            "This feature is no longer available."
        )
