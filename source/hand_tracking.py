"""Hand tracking functions using the intel realsense camera."""

import random
import time


class HandSensor:
    def __init__(self):
        self.name = "Hand Landmarks"
        
    def read(self):
        data = [[random.random(), random.random(), random.random()] for _ in range(21)]
        return {
            "timestampe": time.time(),
            "data": data,
            "source": self.name,
        }