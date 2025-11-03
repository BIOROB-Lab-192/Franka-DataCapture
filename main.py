from config_file import *
import time
import threading
import numpy as np
from datetime import datetime

from source.EMG import EMG
from source.expression import Expression
from source.fNIRS import fNIRS
from source.hand_tracking import HandSensor
from source.webcam import Camera
from source.robot import Robot

from utils.output_meta import OutputBuilder
from utils.video_writer import VideoWriter
from utils.data_coordinator import DataCoordinator
from utils.CSV_writer import CSVWRiter

brain = fNIRS()
emg = EMG()
expression = Expression()
hand = HandSensor()
cam = Camera()

#  connect to robot
franka  = Robot()
franka.connect(hostname, username, password, gripper_toggle=False)
franka.move_to_start()

sensor_list = [expression, hand, emg, franka, fNIRS]

sensor_names = [sensor_list.name for sensor in sensor_list]

csv_fields = ["timestamp", "date_time"] + sensor_names

#  Build output directory
out_build = OutputBuilder(output_dir, save_dir, identity)
out_build.make_directory()
out_build.make_csv()

csv_writer = CSVWRiter(fields=csv_fields, filepath=out_build.csv_path)





def main():
    print("Hello from franka-datacapture!")


if __name__ == "__main__":
    main()
