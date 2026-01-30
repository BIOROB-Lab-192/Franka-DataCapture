"""Webcam recording functions"""

import time
import numpy as np
from vidgear.gears import CamGear, WriteGear
import cv2
import datetime

class Camera:
    def __init__(self, outpath, camera_id, resolution=(1920, 1080), fps=30):
        self.outpath = outpath
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps

        self.name = "webcam"

        # self.stream = CamGear(source=camera_id).start()

        self.cam = CamGear(source=camera_id, resolution=resolution, logging=False).start()
        self.writer = WriteGear(
            output=self.outpath,
            compression_mode=True,
            logging=False, 
            **{
                "-input_framerate": fps,
                "-r": fps,
                "-vcodec": "libx264",
                "-preset": "fast",
                "-pix_fmt": "yuv420p",
            },
        )

    def _overlay_timestamp(self, frame):
        unix_time = time.time()
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cv2.putText(frame, f"Unix: {unix_time:.3f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Local: {local_time}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame

    def get_image(self):
        frame = self.cam.read()
        if frame is None:
            return None
        return frame
    
    def get_and_write(self):
        frame = self.get_image()
        if frame is not None:
            self._overlay_timestamp(frame)
            self.writer.write(frame)
        return frame

    def read(self):
        frame = self.get_image()
        if frame is None:
            cap = False
        else:
            self.write_image(frame)
            cap = True
        return {
            "timestamp": time.time(),
            "data": {"frame_captured": cap},
            "source": self.name,
        }

    def release(self):
        self.cam.stop()
        self.writer.close()

if __name__ == "__main__":
    frames = 0
    start = time.time()
    cam = Camera()
    while time.time() - start < 10:
        frame = cam.read()
        cam.save_frame(frame)
        frames += 1

    actual_fps = frames / (time.time() - start)
    print("Actual FPS:", actual_fps)