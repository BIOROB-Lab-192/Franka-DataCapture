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

 def generate_random_epochs(
    n_epochs: int = 10,
    n_channels: int = 16,
    samples_per_epoch: int = 100,
    sample_rate: float = 10.0,
    seed: int | None = None,
):
    """
    Return a list of simple epoch strings.
    """
    epochs = []
    for i in range(n_epochs):
        epochs.append(f"epoch{i+1}")
    return epochs


def random_epoch_dict(
    n_channels: int = 16,
    samples_per_epoch: int = 100,
    sample_rate: float = 10.0,
    seed: int | None = None,
):
    """
    Convenience: return one random epoch in the system's standard dict format.
    """
    return {
        "timestamp": time.time(),
        "data": "epoch1",
        "source": "fNIRS",
    }
