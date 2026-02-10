"""Functions and code for data capture from emg sensors."""

import random
import time
import socket


class EMG:
    def __init__(self, ip, port=5566):
        self.name = "emg"
        self.ip = ip

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.client.connect(ip, port)

    def send(self, ping_string):
        self.client.send(ping_string)

    def close(self):
        self.client.close()

    def read(self):
        return {
            "timestamp": time.time(),
            "data": {"node1": random.random(), 
                     "node2": random.random(),
                     "node3": random.random()
                     },
            "source": self.name,
        }