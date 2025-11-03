"""Webcam recording functions"""

import time
import numpy as np
import cv2

class Camera:
    def __init__(self, outpath, width=1920, height=1080, fps=60):
        self.output_path = outpath
        self.width = width
        self.height = height
        self.fps = fps
        self.opened = True
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.writer = cv2.VideoWriter(self.output_path, self.fourcc, self.fps, (self.width, self.height))

    def read(self):  # dummy webcam read function creating a stream of numpy arrays
        frame = np.full((self.height, self.width, 3), (203, 192, 255), dtype=np.uint8) 

        return frame

    def save_frame(self, frame):
        timestamp = time.time()
        cv2.putText(
            frame,
            str(timestamp),
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
            )
        self.writer.write(frame)

    def release(self):
        # release webcam too
        self.writer.release()

