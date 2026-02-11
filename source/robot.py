"""Functions for the control of the robot and its data capture process"""

from pylibfranka import Robot, Torques
import time
import multiprocessing

class Franka:
    def __init__(self, IP):
        self.name = "Franka"
        self.IP = IP
        self.zero_torque = Torques([0.0] * 7)
        self.zero_torque.motion_finished = False

    def connect(self):
        self.robot = Robot(self.IP)
        self.torque_thresholds()

        self.active_control = self.robot.start_torque_control()

        float_thread = multiprocessing.Process(target=self.floating, daemon=True)

        float_thread.start()

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
        while True:
            robot_state, duration = self.active_control.readOnce()
            self.active_control.writeOnce(self.zero_torque)

    def stop(self):
        self.robot.stop()

    def extract_data(self, data):
        out = data.EE_T_K
        return out

    def read(self):
        state = self.robot.read_once()
        data = self.extract_data(state)
        return {
            "timestamp": time.time(),
            "data": str(data),
            "source": self.name
        }    

if __name__ == "__main__":
    # Test the Robot class with mock data
    
    robot = Franka()
    robot.connect()
    for i in range(5):
        data = robot.read()
        print(f"Sample data: {data}")
        time.sleep(1)
    robot.stop()