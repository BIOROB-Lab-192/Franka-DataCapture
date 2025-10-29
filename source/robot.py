"""Functions for the control of the robot and its data capture process"""

import random
import time


class Expression:
    def __init__(self):
        self.name = "robot"

    def read(self):
        return {
            "timestamp": time.time(),
            "data": {"robot1": random.randint(0, 1), 
                     "robot2": random.random(),
                     "robot3": random.random()
                     },
            "source": self.name,
        }