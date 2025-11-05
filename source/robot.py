"""Functions for the control of the robot and its data capture process"""
"""
Robot control class for Franka Emika Panda using panda-py.
Encapsulates connection, teaching, trajectory logging, and replay.
"""

import time
import ast
import pickle
import csv
import logging
import numpy as np
import sys
from panda_py import Panda, controllers, libfranka
import panda_py

logging.basicConfig(level=logging.INFO)


class Robot:
    def __init__(self):
        self.name = "Robot"

    def connect(self, hostname, username, password, gripper_toggle):
        self.desk = panda_py.Desk(hostname, username, password) #Host, User, Pass to be read from a separate file
        self.desk.activate_fci()
        self.panda = panda_py.Panda(hostname)
        if gripper_toggle == True:
            self.gripper = libfranka.Gripper(hostname)
        # self.log = panda.get_log() Maybe don't want logging

    # TEACHING MODE
    def start_teaching(self):
        self.panda.teaching_mode(True)

    def stop_teaching(self):
        self.panda.teaching_mode(False)

    # GET STARTING POS
    def start_pos(self, filename):
        with open(filename, "rb") as f:
            loaded_data = pickle.load(f)
            sq = loaded_data['q']
        return sq[-1]

    # BASIC MOVEMENT COMMANDS
    def move_to_joint_position(self, q_goal, speed_factor=0.1):
        self.panda.move_to_joint_position(q_goal, speed_factor=speed_factor)

    def move_to_start(self):
        self.panda.move_to_start()

    # PICKLE FILE LOGGING AND CSV CONVERSION
    def _save_pickle(self, data, filename):
        with open(filename, "wb") as f:
            pickle.dump(data, f)
        logging.info(f"✅ Data written to {filename}")

    def _load_pickle(self, filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    
    def _convert_to_csv(self, filename_in: str, filename_out:str):

        loaded_data = self._load_pickle(self, filename_in)

        # Extract signals
        O_T_EE = loaded_data['O_T_EE']
        q = loaded_data['q']
        dq = loaded_data['dq']
        tau_J = loaded_data['tau_J']
        tau_ext_hat_filtered = loaded_data['tau_ext_hat_filtered']
        K_F_ext_hat_K = loaded_data['K_F_ext_hat_K']
        O_F_ext_hat_K = loaded_data['O_F_ext_hat_K']
        time_data = loaded_data['time']  # Not needed for Haider's

        # Flatten time array of arrays to list of floats
        time_data = [float(t[0]) for t in time_data]

        # Compute relative time BEFORE using it
        time_start = time_data[0]
        rel_time = [(t - time_start) + 1 for t in time_data]
        rel_time[0] = 1.0

        # Make sure all arrays have same length (take min length)
        n = min(len(O_T_EE), len(q), len(dq), len(tau_J),
                len(tau_ext_hat_filtered), len(K_F_ext_hat_K),
                len(O_F_ext_hat_K), len(rel_time))

        data = []

        for j in range(n):
            # EE position from flattened 4x4 matrix (indices 12,13,14)
            T = O_T_EE[j]
            x, y, z = T[12], T[13], T[14]

            # Flatten joint data & forces
            q_i = list(q[j])
            dq_i = list(dq[j])
            tau_J_i = list(tau_J[j])
            tau_ext_i = list(tau_ext_hat_filtered[j])
            K_F_i = list(K_F_ext_hat_K[j])
            O_F_i = list(O_F_ext_hat_K[j])

            t = rel_time[j]

            # Combine all data into one row
            row = [t, x, y, z] + q_i + dq_i + tau_J_i + tau_ext_i + K_F_i + O_F_i
            data.append(row)

        headers = (
            ['time (ms)', 'x (m)', 'y (m)', 'z (m)'] +
            [f'q{k+1}' for k in range(7)] +
            [f'dq{k+1}' for k in range(7)] +
            [f'tau_J{k+1}' for k in range(7)] +
            [f'tau_ext{k+1}' for k in range(7)] +
            [f'K_F_{axis}' for axis in ['Fx', 'Fy', 'Fz', 'Tx', 'Ty', 'Tz']] +
            [f'O_F_{axis}' for axis in ['Fx', 'Fy', 'Fz', 'Tx', 'Ty', 'Tz']]
        )

        with open(filename_out, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)

        logging.info(f"{filename_in} was successfully converted to .csv as {filename_out}.")
    

    # RECORDING TRAJECTORY AND POSITIONAL DATA
    '''Delay float is there in case you need to run over to the franka for singler person tests'''
    def record_start_position(self, filename: str, record_time: int = 10, delay: float = 0):
        self.move_to_start()
        input(f"Press Enter to record start pose (you have {record_time}s).")
        time.sleep(delay)
        self.panda.teaching_mode(True)
        self.panda.enable_logging(record_time * 1000)
        time.sleep(record_time)
        self.panda.teaching_mode(False)

        log = self.panda.get_log()
        self._save_pickle(log, f"{filename}.pickle")

        logging.info(f"Start position saved as {filename}.pickle")
        return log

    def record_trajectory(self, start_q, filename: str, record_time: int, delay: float = 0):
        input("Move to start position and press Enter to continue.")
        self.move_to_joint_position(start_q, speed_factor=0.1)

        input(f"Press Enter to record trajectory ({record_time}s).")
        time.sleep(delay)
        self.panda.teaching_mode(True)
        self.panda.enable_logging(record_time * 1000)
        time.sleep(record_time)
        self.panda.teaching_mode(False)

        log = self.panda.get_log()
        self._save_pickle(log, f"{filename}_LEN-{record_time}.pickle")

        logging.info(f"Trajectory recorded: {filename}_LEN-{record_time}.pickle")
        return log

    def replay_trajectory(self, log_filename: str, record_time: int):
        '''BE SURE "record_time matches" that listed on "log_filename" otherwise out of range error may occur'''
        log = self._load_pickle(log_filename)
        q = log["q"]
        dq = log["dq"]

        input("Press Enter to move to start position.")
        self.move_to_joint_position(q[0], speed_factor=0.1)

        i = 0
        ctrl = controllers.JointPosition()
        self.panda.start_controller(ctrl)

        logging.info("Replaying trajectory...")
        with self.panda.create_context(frequency=1000, max_runtime=record_time) as ctx:
            while ctx.ok():
                ctrl.set_control(q[i], dq[i])
                i += 1
        
        
        logging.info("Trajectory replay complete.")

        input("Press Enter to return to start position.")
        self.move_to_joint_position(q[0], speed_factor=0.1)

    # DATA COLLECTION MODE
    def run_teaching_mode(self, start_q, taskname: str, taskno: str,
                          trials: int, record_time: int, delay: float = 0):
        for i in range(trials):
            pickle_name = f"{taskno}_{taskname}_{i+1}.pickle"
            csv_name = f"{taskno}_{taskname}_{i+1}.csv"

            input(f"Trial {i+1}: Press enter to move to starting position")
            self.move_to_joint_position(start_q, speed_factor=0.1)

            input(f"Press Enter to start trial {i+1} ({record_time} s to move).")
            time.sleep(delay)
            self.panda.teaching_mode(True)
            self.panda.enable_logging(record_time * 1000)
            time.sleep(record_time)
            self.panda.teaching_mode(False)

            log = self.panda.get_log()
            self._save_pickle(log, pickle_name)
            self._convert_to_csv(log, pickle_name, csv_name)
            logging.info(f"✅ Trial {i+1} complete. Data saved.")

    def read(self):
        state = self.panda.get_state()
        return {
            "timestamp": time.time(),
            "data": ast.literal_eval(str(state)),
            "source": self.name
        }
    
if __name__ == "__main__":
    # Test the Robot class with mock data
    robot = Robot(mock=True)
    print("Robot initialized with mock data")
    data = robot.read()
    print(f"Sample data: {data}")
