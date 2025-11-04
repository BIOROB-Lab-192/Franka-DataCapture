"""Functionality for capturing data using MNE python for NIRx devices"""

import time
from pylsl import StreamInfo, StreamOutlet # import required classes


class fNIRS:
    def __init__(self):
        self.name = "fnirs"
        self.info = StreamInfo(name='Trigger', type='Markers', channel_count=1, channel_format='int32', source_id='Example') # sets variables for object info
        self.outlet = StreamOutlet(self.info) # initialize stream.
        self.current_marker = None

    def send_markers(self, marker):
        self.outlet.push_sample(x=[marker])
        self.current_marker = marker

    def read(self):
        epoch_marker = self.current_marker if self.current_marker is not None else 0
        return {
            "timestamp": time.time(),
            "data": {"epoch": epoch_marker},
            "source": self.name,
        }
