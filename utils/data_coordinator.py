"""Data coordinator to synchronize data from different sources and write to CSV.

This coordinator aligns rows by a common anchor timestamp (milliseconds precision)
to handle sensor-specific capture latencies. Slower sensors can arrive later,
but their data is merged into the correct row keyed by the anchor timestamp.
"""

import time
import datetime
import threading

from utils.CSV_writer import CSVWRiter


class DataCoordinator:
    def __init__(self, output_builder, required_sources=None, max_skew_ms=50, max_wait_ms=200):
        """Initialize the data coordinator.

        Args:
            output_builder: OutputBuilder instance to manage file paths
            required_sources: Iterable of source keys required for a complete row.
                Defaults to {"emg", "expression", "hand", "robot", "fnirs"}.
            max_skew_ms: Maximum timestamp difference to consider the same row.
            max_wait_ms: Max time to wait before flushing an incomplete row.
        """
        self.output_builder = output_builder

        # Row buffers keyed by anchor timestamp (rounded to ms)
        # Each entry: {
        #   "anchor_ts": float,
        #   "created_at": float,
        #   "last_update": float,
        #   "data": {source_name: payload_dict}
        # }
        self.rows = {}
        self.lock = threading.Lock()

        # Define CSV fields based on requirements
        self.csv_fields = [
            "timestamp",
            "date_time",
            "expression",
            "hand_tracking",
            "EMG",
            "robot",
            "fNIRS",
        ]
        self.csv_writer = None

        # Completion policy and timing
        self.required_sources = set(required_sources or {"emg", "expression", "hand", "robot", "fnirs"})
        self.max_skew_secs = max_skew_ms / 1000.0
        self.max_wait_secs = max_wait_ms / 1000.0
        self.closed = False
        
    def initialize_csv(self):
        """Initialize the CSV writer."""
        self.output_builder.make_directory()
        self.output_builder.make_csv()
        
        self.csv_writer = CSVWRiter(self.output_builder.csv_path, self.csv_fields)
        self.csv_writer.open_csv()
        self.closed = False
        
    def add_data(self, source_name, data):
        """Add data from a source to the appropriate row bucket.

        Args:
            source_name: Name of the data source (e.g., "emg", "expression")
            data: Dict containing at least {"timestamp": float, "data": Any}
        """
        timestamp = data.get("timestamp", time.time())

        with self.lock:
            if self.closed or self.csv_writer is None:
                return
            row_key = self._find_or_create_row(timestamp)
            entry = self.rows[row_key]
            entry["data"][source_name] = data
            entry["last_update"] = time.time()

            # Try to write rows whenever new data arrives
            self._try_write_rows()
            
    def _try_write_rows(self):
        """Write complete or timed-out rows and cleanup buffers."""
        if self.closed or self.csv_writer is None:
            return
        to_write = []
        for row_key, entry in list(self.rows.items()):
            if self._row_is_complete(entry) or self._should_flush(entry):
                to_write.append(row_key)

        for row_key in to_write:
            entry = self.rows.pop(row_key)
            row = self._format_row(entry)
            self.csv_writer.write_row(row)

    def _find_or_create_row(self, timestamp):
        """Find an existing row within skew tolerance, or create a new one."""
        anchor_key = round(timestamp * 1000) / 1000.0
        now = time.time()

        for existing_key, _ in self.rows.items():
            if abs(timestamp - existing_key) <= self.max_skew_secs:
                return existing_key

        self.rows[anchor_key] = {
            "anchor_ts": anchor_key,
            "created_at": now,
            "last_update": now,
            "data": {},
        }
        return anchor_key

    def _row_is_complete(self, entry):
        present = set(entry["data"].keys())
        return self.required_sources.issubset(present)

    def _should_flush(self, entry):
        age = time.time() - entry["created_at"]
        return age >= self.max_wait_secs
    
    def _format_row(self, entry):
        """Format the row data for CSV writing using the entry's anchor timestamp."""
        timestamp = entry["anchor_ts"]

        dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        date_time = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        row = {
            "timestamp": timestamp,
            "date_time": date_time,
        }

        data = entry["data"]

        # Expression
        if "expression" in data and data["expression"] is not None:
            expression_data = data["expression"]["data"]
            happy_not = "happy" if expression_data.get("happy/not") == 1 else "sad"
            row["expression"] = happy_not
        else:
            row["expression"] = ""

        # Hand tracking
        if "hand" in data and data["hand"] is not None:
            row["hand_tracking"] = str(data["hand"]["data"])
        else:
            row["hand_tracking"] = ""

        # EMG
        if "emg" in data and data["emg"] is not None:
            row["EMG"] = str(data["emg"]["data"])
        else:
            row["EMG"] = ""

        # Robot
        if "robot" in data and data["robot"] is not None:
            row["robot"] = str(data["robot"]["data"])
        else:
            row["robot"] = ""

        # fNIRS - now returns simple strings like "epoch1", "epoch2", etc.
        if "fnirs" in data and data["fnirs"] is not None:
            fnirs_data = data["fnirs"]["data"]
            # Handle both string data (new format) and any legacy format
            if isinstance(fnirs_data, str):
                row["fNIRS"] = fnirs_data
            else:
                row["fNIRS"] = str(fnirs_data)
        else:
            row["fNIRS"] = ""

        return row
    
    def close(self):
        """Close the CSV writer."""
        with self.lock:
            self.closed = True
            # Flush any remaining buffered rows
            for _, entry in list(self.rows.items()):
                row = self._format_row(entry)
                if self.csv_writer:
                    self.csv_writer.write_row(row)
            self.rows.clear()
        if self.csv_writer:
            self.csv_writer.close()