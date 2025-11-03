"""Demo script to demonstrate the data capture functionality."""

import time
import threading
import numpy as np
from datetime import datetime

from source.EMG import EMG
from source.expression import Expression
from source.fNIRS import random_epoch_dict
from source.hand_tracking import HandSensor
from source.webcam import Camera
from source.robot import Robot

from utils.output_meta import OutputBuilder
from utils.video_writer import VideoWriter
from utils.data_coordinator import DataCoordinator


def simulate_data_capture(duration=10):
    """Simulate data capture from different sources.
    
    Args:
        duration: Duration of the simulation in seconds
    """
    # Create output directory based on current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "output"
    save_dir = f"run_{timestamp}"
    identity = f"experiment_{timestamp}"
    
    # Initialize output builder
    output_builder = OutputBuilder(output_dir, save_dir, identity)
    
    # Initialize data coordinator
    coordinator = DataCoordinator(output_builder)
    coordinator.initialize_csv()
    
    # Initialize video writer
    video_writer = VideoWriter(output_builder.save_dir, identity)
    
    # Initialize data sources
    emg_sensor = EMG()
    expression_sensor = Expression()
    hand_sensor = HandSensor()
    robot_sensor = Robot(mock=True)  # Use mock mode to load data from CSV
    camera = Camera(str(output_builder.save_dir / f"{identity}_webcam.avi"))
    
    print(f"Starting data capture for {duration} seconds...")
    start_time = time.time()
    
    # Simulate data capture with different latencies
    expression_threads = []
    while time.time() - start_time < duration:
        # Capture EMG data (fast)
        emg_data = emg_sensor.read()
        coordinator.add_data("emg", emg_data)
        
        # Capture hand tracking data (medium speed)
        hand_data = hand_sensor.read()
        coordinator.add_data("hand", hand_data)
        
        # Capture robot data
        robot_data = robot_sensor.read()
        coordinator.add_data("robot", robot_data)
        
        # Capture fNIRS data (new simplified format)
        fnirs_data = random_epoch_dict()
        coordinator.add_data("fnirs", fnirs_data)
        
        # Capture webcam frame
        frame = camera.read()
        timestamp = video_writer.write_frame(frame)
        
        # Simulate expression data with latency (slow)
        def capture_expression_with_delay():
            # Simulate processing delay for expression recognition
            time.sleep(0.5)  # 500ms delay
            expression_data = expression_sensor.read()
            # Use the original timestamp despite the delay
            expression_data["timestamp"] = timestamp
            coordinator.add_data("expression", expression_data)
        
        # Start expression recognition in a separate thread and track it
        t = threading.Thread(target=capture_expression_with_delay)
        t.start()
        expression_threads.append(t)
        
        # Sleep to simulate real-time capture
        time.sleep(0.1)
    
    # Wait for any outstanding expression threads to finish
    for t in expression_threads:
        t.join()

    # Cleanup
    video_writer.release()
    coordinator.close()
    print(f"Data capture completed. Files saved to {output_builder.save_dir}")


if __name__ == "__main__":
    simulate_data_capture(duration=10)