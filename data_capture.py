"""Functions integrating all the sensors into one script, writing a csv file with time stamps."""

import asyncio
from collections import defaultdict
import time

class AsyncDataCapture:
    def __init__(self, sensors, csv_writer, batch_duration):
        self.sensors = sensors
        self.csv_writer = csv_writer
        self.queue = asyncio.Queue()
        self.last_values = defaultdict(dict)
        self.running = True
        self.batch_time = batch_duration

    async def start(self):
        # Start async tasks
        sensor_tasks = [asyncio.create_task(self._sensor_loop(s)) for s in self.sensors]
        writer_task = asyncio.create_task(self._writer_loop())
        await asyncio.gather(*sensor_tasks, writer_task)

    async def _sensor_loop(self, sensor):
        """Read from sensor continuosly."""
        while self.running:
            reading = sensor.read()
            await self.queue.put(reading)
            await asyncio.sleep(0)

    async def _writer_loop(self):
        """Writes merged data rows using the provided CSV writer."""
        while self.running:
            reading = await self.queue.get()
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