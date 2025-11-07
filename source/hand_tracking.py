"""Hand tracking functions using the intel realsense camera."""

from realsense_mediapipe_tracking.camera import realsenseCamera
from realsense_mediapipe_tracking.hand_tracking import handTrack
import time
import multiprocessing as mp

class HandSensor:
    def __init__(self):
        self.name = "hand_landmarks"
        self.queue = mp.Queue(maxsize=1)
        self.process = mp.Process(target=self._capture_loop, daemon=True)
        self.process.start()

    def _capture_loop(self):
        cam = realsenseCamera()
        tracker = handTrack(cam)

        while True:
            color_image, depth_image, depth_frame = tracker.cam.get_frames()
            if color_image is None or depth_image is None:
                time.sleep(0.005)
                continue

            landmarks_xyz, results = tracker.tracking(color_image, depth_frame)

            landmark_dict = {}
            for i, v in enumerate(landmarks_xyz):
                landmark_dict[f"mark_{i}"] = v

            if not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except:
                    pass
            self.queue.put(landmark_dict)

    def stop(self):
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
        
    def read(self):
        if not self.queue.empty():
            data = self.queue.get_nowait()
        return {
            "timestamp": time.time(),
            "data": data,
            "source": self.name,
        }