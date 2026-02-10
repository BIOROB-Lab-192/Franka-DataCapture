"""Functions for the control of the robot and its data capture process"""

from pylibfranka import Robot, Torques
import time
import ast

class Rob:
    def __init__(self, IP):
        self.name = "Robot"
        self.IP = IP
    
    def connect(self):
        self.rob = Robot(self.IP)
        # self.free_float()

        self.active_control = robot.start_torque_control()
        zero_torque = Torques([0.0] * 7)
        zero_torque.motion_finished = False
        self.active_control.writeOnce(zero_torque)

    def free_float(self):
        lower_torque_thresholds = [1e6] * 7
        upper_torque_thresholds = [1e6] * 7
        lower_force_thresholds = [1e6] * 6
        upper_force_thresholds = [1e6] * 6

        self.rob.set_collision_behavior(
            lower_torque_thresholds,
            upper_torque_thresholds,
            lower_force_thresholds,
            upper_force_thresholds,
        )

    def stop(self):
        self.rob.stop()

    def read(self):
        state = self.rob.read_once()
        return {
            "timestamp": time.time(),
            "data": ast.literal_eval(str(state)),
            "source": self.name
        }    

if __name__ == "__main__":
    # Test the Robot class with mock data
    
    robot = Rob()
    robot.connect()
    for i in range(5):
        data = robot.read()
        print(f"Sample data: {data}")
        time.sleep(1)
    robot.stop()