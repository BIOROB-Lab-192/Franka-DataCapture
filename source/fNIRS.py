"""Functionality for capturing data using MNE python for NIRx devices"""

import time
from pylsl import StreamInfo, StreamOutlet # import required classes


class fNIRS:
    def __init__(self):
        self.name = "fnirs"
        self.info = StreamInfo(name='Trigger', type='Markers', channel_count=1, channel_format='int32', source_id='Example') # sets variables for object info
        self.outlet = StreamOutlet(self.info) # initialize stream.

    def send_singal(self, marker):
        self.outlet.push_sample(x=marker)

    def read(self):
        return {
            "timestamp": time.time(),
            "data": "stuff",
            "source": self.name,
        }
