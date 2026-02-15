import multiprocessing
import time
from pylibfranka import Robot, Torques
import queue

class Franka:
    def __init__(self, IP):
        self.name = "Franka"
        self.IP = IP
        self.data_queue = multiprocessing.Queue(maxsize=1)
        self.stop_signal = multiprocessing.Event()

    def connect(self):
        self.process = multiprocessing.Process(target=self._control_loop, daemon=True)
        self.process.start()

    def _control_loop(self):
        try:
            robot = Robot(self.IP)
            robot.set_collision_behavior([1e6]*7, [1e6]*7, [1e6]*6, [1e6]*6)
            
            zero_torque = Torques([0.0] * 7)
            active_control = robot.start_torque_control()
            
            print("Robot control started (Dynamic Queue Mode)...")
            
            while not self.stop_signal.is_set():
                state, _ = active_control.readOnce()
                
                # 1. Dynamic Extraction (No hard-coding sizes!)
                data = self.extract_data(state)
                
                # 2. Non-blocking Queue Push
                # We try to put the data. If the queue is full, we swap the old data for the new.
                try:
                    self.data_queue.put_nowait(data)
                except queue.Full: 
                    # Queue is full, meaning the main process is slow. 
                    # We clear the old frame to make room for the fresh one.
                    try:
                        self.data_queue.get_nowait()
                        self.data_queue.put_nowait(data)
                    except queue.Empty:
                        pass
                
                # 3. Write command immediately to satisfy 1kHz constraint
                active_control.writeOnce(zero_torque)
                
        except Exception as e:
            print(f"Robot control Error: {e}")
        finally:
            print("Control loop exiting...")

    def extract_data(self, state):
        """
        Robot properties to be extracted from the read datafile. Change as needed.
        """
        return {
            "ee": list(state.O_T_EE),
            "q": list(state.q),
            "dq": list(state.dq),
            "tau_J": list(state.tau_J),
            "robot_time": state.time.toMS()
        }

    def read(self):
        if not self.data_queue.empty():
            data = self.data_queue.get()
            return {
                "timestamp": time.time(),
                "data": data,
                "source": self.name,
            }


    def stop(self):
        print("Stopping Franka...")
        self.stop_signal.set()
        if hasattr(self, "process"):
            self.process.join(timeout=1)
            if self.process.is_alive():
                self.process.terminate()

if __name__ == "__main__":
    robot = Franka(IP="10.31.82.199")
    robot.connect()
    
    try:
        for _ in range(20):
            sample = robot.read()
            if sample:
                # Dynamically access whatever keys you added in extract_data
                print(f"Time: {sample['data']['robot_time']} | Q[0]: {sample['data']['q'][0]:.3f}")
            time.sleep(0.5)
    finally:
        robot.stop()