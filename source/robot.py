import multiprocessing
import queue
import time

from pylibfranka import Robot, Torques


class Franka:
    def __init__(self, IP):
        self.name = "Franka"
        self.IP = IP
        self.data_queue = multiprocessing.Queue(maxsize=1)
        self.stop_signal = multiprocessing.Event()

    def connect(self):
        self.process = multiprocessing.Process(
            target=self._control_loop,
            args=(self.data_queue, self.stop_signal),
            daemon=True,
        )
        self.process.start()

    def _control_loop(self, data_queue, stop_signal):
        try:
            robot = Robot(self.IP)
            robot.set_collision_behavior([1e6] * 7, [1e6] * 7, [1e6] * 6, [1e6] * 6)

            zero_torque = Torques([0.0] * 7)
            active_control = robot.start_torque_control()

            print("Robot control started (Dynamic Queue Mode)...")

            while not stop_signal.is_set():
                state, _ = active_control.readOnce()
                active_control.writeOnce(zero_torque)

                data = self.extract_data(state)

                try:
                    data_queue.put_nowait(data)
                except queue.Full:
                    try:
                        data_queue.get_nowait()
                        data_queue.put_nowait(data)
                    except queue.Empty:
                        pass

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
        }

    def read(self):
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
                print(
                    f"Time: {sample['timestamp']} | Q[0]: {sample['data']['q'][0]:.3f}"
                )
            time.sleep(0.5)
    finally:
        robot.stop()
