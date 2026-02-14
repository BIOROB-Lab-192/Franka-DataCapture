"""Functions integrating all the sensors into one script, writing a csv file with time stamps."""

import asyncio
from collections import defaultdict
import time

class AsyncDataCapture:
    def __init__(self, sensors, csv_writer, batch_duration):
        self.sensors = sensors
        self.csv_writer = csv_writer
        self.queue = asyncio.Queue(maxsize=200)
        self.last_values = defaultdict(dict)
        self.running = True
        self.batch_time = batch_duration

    async def start(self):
        # Start async tasks
        sensor_tasks = [asyncio.create_task(self._sensor_loop(s)) for s in self.sensors]
        writer_task = asyncio.create_task(self._writer_loop())
        await asyncio.gather(*sensor_tasks, writer_task)

    async def _sensor_loop(self, sensor):
        """Read from sensor continuously."""
        failure_count = 0
        while self.running:
            try:
                # Run potentially blocking sensor.read() in a thread
                reading = await asyncio.to_thread(sensor.read)
                try:
                    # Try to add normally
                    self.queue.put_nowait(reading)
                except asyncio.QueueFull:
                    try:
                        _ = self.queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                    try:
                        self.queue.put_nowait(reading)
                    except asyncio.QueueFull:
                        pass
                failure_count = 0
            except Exception as e:
                failure_count += 1
                # Warn to console so unplug / failures are visible immediately
                print(f"[!] Sensor error ({sensor.name}):\n{e}")
                # Enqueue an error reading so the writer loop can react if desired
                await self.queue.put({
                    "timestamp": time.time(),
                    "data": {"error": str(e)},
                    "source": sensor.name,
                })
            await asyncio.sleep(0)

    async def _writer_loop(self):
        """Writes merged data rows CSV writer."""
        while self.running:
            # periodically wake up to re-check self.running
            try:
                reading = await asyncio.wait_for(self.queue.get(), timeout=3)
            except asyncio.TimeoutError:
                # timeout lets us re-evaluate self.running and loop again
                continue
            src = reading["source"]
            ts = reading["timestamp"]
            self.last_values[src] = reading["data"]

            start_time = time.monotonic()
            end_time = start_time + self.batch_time
            while time.monotonic() < end_time:
                timeout = end_time - time.monotonic()
                if timeout <= 0:
                    break
                try:
                    next_reading = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                    self.last_values[next_reading["source"]] = next_reading["data"]
                except asyncio.TimeoutError:
                    break

            row = {"timestamp": ts}
            for s in self.sensors:
                val = self.last_values.get(s.name, {})
                if isinstance(val, dict):
                    for k, v in val.items():
                        row[f"{s.name}_{k}"] = v
                else:
                    row[s.name] = val

            self.csv_writer.write_row(row)

    def stop(self):
        self.running = False