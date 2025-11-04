import asyncio
from config_file import *

from source.EMG import EMG
from source.expression import Expression
from source.fNIRS import fNIRS
from source.hand_tracking import HandSensor
from source.webcam import Camera
from source.robot import Robot

from utils.output_meta import OutputBuilder
from utils.CSV_writer import CSVWRiter

from data_capture import AsyncDataCapture

brain = fNIRS()
emg = EMG()
expression = Expression()
hand = HandSensor()
cam = Camera()

#  connect to robot
franka  = Robot()
franka.connect(hostname, username, password, gripper_toggle=False)
franka.move_to_start()

franka.start_teaching()

sensor_list = [franka, brain]
sensor_names = [s.name for s in sensor_list]

csv_fields = ["timestamp"]
for sensor in sensor_list:
    sample = sensor.read()
    if isinstance(sample["data"], dict):
        for key in sample["data"].keys():
            csv_fields.append(f"{sensor.name}_{key}")
    else:
        csv_fields.append(sensor.name)


#  Build output directory
out_build = OutputBuilder(output_dir, save_dir, identity)
out_build.make_directory()
out_build.make_csv()

csv_writer = CSVWRiter(fields=csv_fields, filepath=out_build.csv_path)
csv_writer.open_csv()

capture = AsyncDataCapture(sensor_list, csv_writer, 0.010)

async def send_markers(brain_sensor):
    active_counter = 1
    send_zero_next = False

    while True:
        await asyncio.to_thread(input, "Press Enter to send next marker: ")

        if send_zero_next:
            marker = 0
            send_zero_next = False
        else:
            marker = active_counter
            active_counter += 1
            send_zero_next = True

        brain_sensor.send_marker(marker)

async def main():
    task_capture = asyncio.create_task(capture.start())
    task_markers = asyncio.create_task(send_markers(brain))
    await asyncio.gather(task_capture, task_markers)

try:
    asyncio.run(main())
finally:
    franka.stop_teaching()
    capture.stop()
    csv_writer.close()