"""Functions for the control of the robot and its data capture process"""

import time
import logging
import csv
import os
import random
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Comment out imports that might not be available in mock mode
# import panda_py
# from panda_py import libfranka
# from panda_py import controllers


class Robot:
    def __init__(self, mock=True):
        self.name = "robot"
        self.mock = mock
        self.mock_data = []
        self.current_index = 0
        
        # Load mock data if in mock mode
        if self.mock:
            self._load_mock_data()

    def _load_mock_data(self):
        """Load mock data from CSV file"""
        csv_path = Path(os.path.dirname(os.path.dirname(__file__))) / "Tyler_Test-Excercise_1.csv"
        
        try:
            with open(csv_path, 'r') as f:
                csv_reader = csv.reader(f)
                header_skipped = False
                for row in csv_reader:
                    if not header_skipped:
                        # Skip the header row
                        header_skipped = True
                        continue
                        
                    if row:  # Skip empty rows
                        try:
                            # Convert all values to float
                            float_row = [float(val) for val in row]
                            self.mock_data.append(float_row)
                        except ValueError:
                            # Skip rows that can't be converted to float
                            continue
            
            logging.info(f"Loaded {len(self.mock_data)} rows of mock data from {csv_path}")
        except Exception as e:
            logging.error(f"Error loading mock data: {e}")
            # Create some default mock data if file can't be loaded
            self.mock_data = [
                [1.0, 0.566, 0.237, 0.023, 0.099, 0.706, 0.285, -1.947, -0.373, 2.630, 1.380],
                [2.0, 0.566, 0.237, 0.023, 0.099, 0.706, 0.285, -1.947, -0.373, 2.630, 1.380]
            ]

    def connect(self, hostname=None, username=None, password=None, gripper_toggle=False):
        """Connect to the robot or initialize mock mode"""
        if not self.mock:
            try:
                self.desk = None  # TODO: Replace with actual implementation
                self.desk.activate_fci()
                self.panda = panda_py.Panda(hostname)
                if gripper_toggle:
                    self.gripper = libfranka.Gripper(hostname)
                logging.info(f"Connected to robot at {hostname}")
            except Exception as e:
                logging.error(f"Failed to connect to robot: {e}")
                self.mock = True
                self._load_mock_data()
        else:
            logging.info("Running in mock mode with pre-recorded data")

    def start_teaching(self):
        """Start teaching mode"""
        if not self.mock:
            # Implement actual teaching mode
            pass
        else:
            logging.info("Mock: Starting teaching mode")

    def stop_teaching(self):
        """Stop teaching mode"""
        if not self.mock:
            # Implement actual teaching mode stop
            pass
        else:
            logging.info("Mock: Stopping teaching mode")

    def read(self):
        """Read data from the robot or return mock data"""
        if not self.mock:
            # Return actual robot data
            return {
                "timestamp": time.time(),
                "data": {k: v[-1] for k, v in self.log.items()},
                "source": self.name
            }
        else:
            # Return mock data
            if not self.mock_data:
                return {
                    "timestamp": time.time(),
                    "data": {},
                    "source": self.name
                }
            
            # Cycle through mock data
            data_row = self.mock_data[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.mock_data)
            
            # Create a dictionary with the data
            # First value is timestamp, rest are robot state values
            data_dict = {
                f"joint_{i}": val for i, val in enumerate(data_row[1:])
            }
            
            return {
                "timestamp": time.time(),
                "data": data_dict,
                "source": self.name
            }

if __name__ == "__main__":
    # Test the Robot class with mock data
    robot = Robot(mock=True)
    print("Robot initialized with mock data")
    data = robot.read()
    print(f"Sample data: {data}")