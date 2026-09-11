# tools/tool_utilities/media.py

class VideoDisplayUnavailableError(RuntimeError):
    """Raised when video display is requested but disabled.

    The video display functionality depended on `cv2` (OpenCV), which has been
    removed from DarkGlitch. This module is kept importable so any lingering
    reference fails with a clear message.
    """


async def show_video(track, stop_event):
    """Video display has been removed from DarkGlitch.

    The video-display functionality depended on the `cv2` (OpenCV) library,
    which has been removed from the project. This function is kept as a stub
    that reports the feature as disabled rather than crashing with a
    `ModuleNotFoundError`.
    """
    raise VideoDisplayUnavailableError(
        "Video display (OpenCV) has been disabled in DarkGlitch. "
        "This feature is no longer available."
    )
