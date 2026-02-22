"""Functions and code for data capture from emg sensors."""

import random
import socket
import time


class EMG:
    def __init__(self, ip, port=5566):
        self.name = "emg"
        self.ip = ip
        self.port = port

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))

    def send(self, ping_string):
        self.client.send(ping_string)

    def close(self):
        self.client.close()

    def read(self):
        return {
            "timestamp": time.time(),
            "data": {
                "node1": random.random(),
                "node2": random.random(),
                "node3": random.random(),
            },
            "source": self.name,
        }


if __name__ == "__main__":
    emg_test = EMG(ip="10.31.81.38", port=5555)
    try:
        while True:
            print("ping")
            emg_test.send("ping".encode())
            time.sleep(3)
    except Exception as E:
        print(E)
    finally:
        emg_test.close()
