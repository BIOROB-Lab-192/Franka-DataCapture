"""Functions for the control of the robot and its data capture process"""

import time
import logging
logging.basicConfig(level=logging.INFO)
import panda_py
from panda_py import libfranka
from panda_py import controllers


class Robot:
    def __init__(self):
        self.name = "robot"

    def connect(self, hostname, username, password, gripper_toggle):
        self.desk = abc # TODO do later
        self.desk.activate_fci()
        self.panda = panda_py.Panda(hostname)
        if gripper_toggle == True:
            self.gripper = libfranka.Gripper(hostname)
        # self.log = panda.get_log() Maybe don't want logging


    def start_teaching(self):
        pass

    def stop_teaching(self):
        pass

    def read(self):
        return{
            "timestamp": time.time(),
            "data": {k: v[-1] for k, v in self.log.items()},  # or from get state thing
            "source": self.name
        }

if __name__ == "__main__":
    print("hello robot")