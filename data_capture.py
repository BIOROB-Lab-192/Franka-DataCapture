"""Functions integrating all the sensors into one script, writing a csv file with time stamps."""

import asyncio
from collections import defaultdict

class AsyncDataCapture:
    def __init__(self, sensors, csv_writer):
        self.sensors = sensors
        self.csv_writer = csv_writer
        self.queue = asyncio.Queue()
        self.last_values = defaultdict(dict)
        self.running = True

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

            row = {"timestamp": ts}
            for s in self.sensors:
                for k, v in self.last_values[s.name].items():
                    row[f"{s.name}_{k}"] = v

            self.csv_writer.write_row(row)

    def stop(self):
        self.running = False
        self.csv_writer.close()
