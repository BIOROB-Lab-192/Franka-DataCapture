import asyncio
import signal

from config_file import *
from data_capture import AsyncDataCapture
from source.EMG import EMG
from source.expression import Expression
from source.fNIRS import fNIRS
from source.hand_tracking import HandSensor
from source.robot import Franka
from source.webcam import Camera
from utils.CSV_writer import CSVWRiter
from utils.output_meta import OutputBuilder

frame_queue = asyncio.Queue(maxsize=1)

brain = fNIRS()
# emg = EMG()
hand = HandSensor()

#  connect to robot
franka = Franka(IP=hostname)
franka.connect()

expression = Expression(model_path, frame_queue)

sensor_list = [franka, brain, expression, hand]
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

cam = Camera(f"{output_dir}/{save_dir}/{vid_out}", 0)

csv_writer = CSVWRiter(filepath=out_build.csv_path, fields=csv_fields)
csv_writer.open_csv()


async def send_markers(brain_sensor, stop_event):
    active_counter = 1
    send_zero_next = False

    while not stop_event.is_set():
        user_input = await asyncio.to_thread(
            input,
            "Press Enter to send next marker, type 'end' to stop sending markers or type 'quit' to end the program: \n",
        )

        if user_input.strip().lower() == "quit":
            print("Quiting...")
            stop_event.set()
            break
        elif user_input.strip().lower() == "end":
            marker = 0
            brain_sensor.send_markers(marker)
            break
        elif user_input.strip().lower() != "":
            print("invalid input.")
            continue

        if send_zero_next:
            marker = 0
            send_zero_next = False
        else:
            marker = active_counter
            active_counter += 1
            send_zero_next = True

        try:
            brain_sensor.send_markers(marker)
        except Exception as e:
            print(f"Error sending marker {marker}: \n {e}")
            break

async def process_frames(camera, capture, stop_event):
    while not stop_event.is_set():
        try:
            frame = await asyncio.to_thread(camera.get_and_write)
            if frame is not None:
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await frame_queue.put(frame)
        except Exception as e:
            print(f"[!] Frame processing error: {e}")
        await asyncio.sleep(0.5)
    print("Frame processing has stopped")


async def main():
    loop = asyncio.get_running_loop()

    stop_event = asyncio.Event()
        
    capture = AsyncDataCapture(sensor_list, csv_writer, 0.5)

    # Handle SIGINT (Ctrl+C)
    def shutdown():
        print("\n[!] Ctrl+C detected, shutting down gracefully...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, shutdown)

    task_capture = asyncio.create_task(capture.start())
    task_markers = asyncio.create_task(send_markers(brain, stop_event))
    task_frames = asyncio.create_task(process_frames(cam, capture, stop_event))

    # Wait for shutdown event
    await stop_event.wait()

    # Graceful stop
    capture.stop()
    await asyncio.sleep(1)
    task_capture.cancel()
    task_markers.cancel()
    task_frames.cancel()

    await asyncio.gather(
        task_capture, task_markers, task_frames, return_exceptions=True
    )

    franka.stop()
    hand.stop()
    cam.release()
    csv_writer.close()


if __name__ == "__main__":
    try:
        print("Start")
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            franka.stop()
        except Exception:
            pass
        try:
            csv_writer.close()
        except Exception:
            pass
        try:
            hand.stop()
        except Exception:
            pass
        try:
            cam.release()
        except Exception:
            pass

    print("Shutdown")
