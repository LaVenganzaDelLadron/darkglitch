from aiortc.contrib.media import MediaPlayer

class WebCam:
    def __init__(self):
        self.player = None
        self.audio = None
        self.video = None

    async def start(self):
        self.player = MediaPlayer("/dev/video0", format="v412", options={"video_size": "640x480", "framerate": "30"})
        self .video = self.player.video
        self .audio = self.player.audio

    async def stop(self):
        if self.player is None:
            return

        stop = getattr(self.player, "stop", None)
        if callable(stop):
            await stop()

    def get_audio_track(self):
        return self.audio

    def get_video_track(self):
        return self.video