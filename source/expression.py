"""Facial expression recognition functions. This will be using a trained pytorch model"""

import random
import time


class Expression:
    def __init__(self):
        self.name = "expression"

    def read(self):
        return {
            "timestamp": time.time(),
            "data": {"happy/not": random.randint(0, 1), "valence/arousal": random.random()},
            "source": self.name,
        }