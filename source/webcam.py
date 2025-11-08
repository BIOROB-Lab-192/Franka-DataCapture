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
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam.")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.writer = cv2.VideoWriter(
            self.output_path, self.fourcc, self.fps, (self.width, self.height)
        )

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from webcam.")
        return frame

    def save_frame(self, frame):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        cv2.putText(
            frame,
            timestamp,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2,
            cv2.LINE_AA
        )
        self.writer.write(frame)

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
        self.writer.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    cam = Camera("test.avi")
    for i in range(300):
        frame = cam.read()
        cam.save_frame(frame)
        time.sleep(1 / cam.fps)
    cam.release()