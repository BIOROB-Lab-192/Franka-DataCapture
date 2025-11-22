"""Hand tracking functions using the intel realsense camera."""
from realsense_mediapipe_tracking.camera import realsenseCamera
from realsense_mediapipe_tracking.hand_tracking import handTrack
import time
import multiprocessing as mp
from pprint import pprint

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
                for j, xyz in enumerate(v):
                    landmark_dict[f"mark_{j}"] = xyz

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
        try:
            data = self.queue.get_nowait()
        except:
            for i in range(21):
                data[f"mark_{i}"] = (float('nan'), float('nan'), float('nan'))
            data = None
        return {
            "timestamp": time.time(),
            "data": data,
            "source": self.name,
        }
    
if __name__ == "__main__":
    hand_sensor = HandSensor()
    try:
        while True:
            data = hand_sensor.read()
            pprint(data, indent=2)
            time.sleep(0.1)
    except KeyboardInterrupt:
        hand_sensor.stop()
    finally:
        hand_sensor.stop()