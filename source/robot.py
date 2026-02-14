"""Functions for the control of the robot and its data capture process"""

import multiprocessing
import time
import ast

from pylibfranka import Robot, Torques


class Franka:
    def __init__(self, IP):
        self.name = "Franka"
        self.IP = IP
        self.zero_torque = Torques([0.0] * 7)
        self.zero_torque.motion_finished = False
        self.stop_signal = None

    def connect(self):
        self.robot = Robot(self.IP)
        self.torque_thresholds()

        self.manager = multiprocessing.Manager()
        self.data_dict = self.manager.dict()
        self.stop_signal = self.manager.Event()

        self.float_thread = multiprocessing.Process(target=self.floating, daemon=True)

        self.float_thread.start()

    def torque_thresholds(self):
        lower_torque_thresholds = [1e6] * 7
        upper_torque_thresholds = [1e6] * 7
        lower_force_thresholds = [1e6] * 6
        upper_force_thresholds = [1e6] * 6

        self.robot.set_collision_behavior(
            lower_torque_thresholds,
            upper_torque_thresholds,
            lower_force_thresholds,
            upper_force_thresholds,
        )

    def floating(self):
        self.active_control = self.robot.start_torque_control()
        try:
            while not self.stop_signal.is_set():
                robot_state, duration = self.active_control.readOnce()
                self.active_control.writeOnce(self.zero_torque)
                data = self.extract_data(robot_state)
                self.data_dict.update(data)
        finally:
            try:
                self.robot.stop()
            except Exception:
                pass

    def stop(self):
        print("Stopping Franka...")

        try:
            if hasattr(self, "float_thread") and self.float_thread.is_alive():
                self.float_thread.join(timeout=2)

                if self.float_thread.is_alive():
                    print("Force terminating Franka process...")
                    self.float_thread.terminate()
                    self.float_thread.join()

        except Exception as e:
            print(f"[!] Error stopping Franka process: {e}")

        try:
            if hasattr(self, "manager"):
                self.manager.shutdown()
        except Exception as e:
            print(f"[!] Error shutting down Manager: {e}")

        print("Franka stopped.")

    def extract_data(self, data):
        eetk = list(data.EE_T_K)
        ee = list(data.O_T_EE)
        q = list(data.q)
        dq = list(data.dq)
        out = {"eetk": eetk, "ee": ee, "q": q, "dq": dq}
        return out

    def read(self):
        while True:
            data = dict(self.data_dict)
            if len(data) == 0:
                time.sleep(0.01)
                continue
            else:
                return {
                    "timestamp": time.time(),
                    "data": ast.literal_eval(str(data)),
                    "source": self.name,
                }


if __name__ == "__main__":
    # Test the Robot class with mock data

    robot = Franka(IP="10.31.82.199")
    robot.connect()
    for i in range(60):
        print("here")
        data = robot.read()
        print(data)
        time.sleep(1)
    robot.stop()
