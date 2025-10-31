"""Functionlaity for capturing data using MNE python for NIRx devices"""

import time

class fNIRS:
    def __init__(self):
        self.name = "fnirs"

    def read(self):
        return {
            "timestamp": time.time(),
            "data": "stuff",
            "source": self.name,
        }