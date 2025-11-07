import asyncio
from config_file import *
import signal

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
# emg = EMG()
# expression = Expression()
# hand = HandSensor()
# cam = Camera()

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

csv_writer = CSVWRiter(filepath=out_build.csv_path, fields=csv_fields)
csv_writer.open_csv()

capture = AsyncDataCapture(sensor_list, csv_writer, 0.010)

async def send_markers(brain_sensor, stop_event):
    active_counter = 1
    send_zero_next = False

    while True:
        user_input = await asyncio.to_thread(input, "Press Enter to send next marker, type 'end' to stop sending markers or type 'quit' to end the program: \n")

        if user_input.strip().lower() == "quit":
            print("Quiting...")
            stop_event.set()
            break
        elif user_input.strip().lower() == "end":
            marker = 0
            brain_sensor.send_markers(marker) 
            break    
        elif user_input.strip().lower() != '':
            print("invalid input.")
            continue

        if send_zero_next:
            marker = 0
            send_zero_next = False
        else:
            marker = active_counter 
            active_counter += 1
            send_zero_next = True

        brain_sensor.send_markers(marker)


async def main():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    # Handle SIGINT (Ctrl+C)
    def shutdown():
        print("\n[!] Ctrl+C detected, shutting down gracefully...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, shutdown)

    task_capture = asyncio.create_task(capture.start())
    task_markers = asyncio.create_task(send_markers(brain, stop_event))

    # Wait for shutdown event
    await stop_event.wait()

    # Graceful stop
    capture.stop()
    task_capture.cancel()
    task_markers.cancel()

    await asyncio.gather(task_capture, task_markers, return_exceptions=True)

try:
    print("Start")
    asyncio.run(main())
except KeyboardInterrupt:
    pass
finally:
    franka.stop_teaching()
    csv_writer.close()
    print("Shutdown")