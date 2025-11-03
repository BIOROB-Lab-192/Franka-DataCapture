"""Functions and code for data capture from emg sensors."""

import random
import time


class EMG:
    def __init__(self):
        self.name = "emg"

    def read(self):
        return {
            "timestamp": time.time(),
            "data": {"node1": random.random(), 
                     "node2": random.random(),
                     "node3": random.random()
                     },
            "source": self.name,
        }