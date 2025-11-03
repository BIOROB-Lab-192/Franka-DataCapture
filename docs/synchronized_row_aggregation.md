# Synchronized Row Aggregation for Latency-Tolerant CSV Writing

## Goal

- Align rows by the same timestamp even when sensors have different capture latencies so the CSV has one row per sample time across EMG, fNIRS, robot, hand, expression.

## What I Changed

- Implemented timestamp-bucketed aggregation in `utils/data_coordinator.py` so data is grouped by an anchor timestamp (millisecond precision) and written in one row.
- Rows are now keyed by the anchor timestamp rather than “latest arrival”. Delayed sources are merged into the correct row when they arrive.
- Added tolerance and timeout:
  - `max_skew_ms` (default `50`) groups readings within ±50 ms into the same row.
  - `max_wait_ms` (default `200`) flushes incomplete rows after a short delay to avoid stalling.

## How It Works

- On `add_data(source, data)` the coordinator:
  - Uses `data['timestamp']` to find an existing row within `max_skew_ms`, or creates a new bucket using that timestamp rounded to milliseconds.
  - Buffers payloads for that row.
  - Writes the row when either all required sources are present or when the row is older than `max_wait_ms` (missing fields are written as empty strings).
- The CSV row’s `timestamp` and `date_time` are taken from the row’s anchor timestamp, keeping rows consistent.

## Configuration

- `required_sources`: defaults to `{'emg','expression','hand','robot','fnirs'}`. You can change this based on what you’re capturing in a run.
- `max_skew_ms`: set slightly larger than your slowest expected latency. For 27 ms expression you can use `40–60 ms`.
- `max_wait_ms`: choose a small value (e.g., `150–300 ms`) to balance completeness vs. throughput.

## Usage Tips

- If you have a natural “anchor” (e.g., webcam frame time or a sampling tick), propagate it to slower sensors so they land in the right bucket:
  - Example: keep what you already do in `data_capture_demo.py` for expression by setting `expression_data['timestamp'] = anchor_ts` where `anchor_ts` is the video frame timestamp.
- For instant sensors (EMG, fNIRS, robot), let them use their own `time.time()`; the coordinator will assign them to the nearest bucket within `max_skew_ms`.

## Example Flow

- Use a single loop to drive sampling; keep slow work off the main thread.
- Keep your current pattern for expression:
- Create anchor per cycle (optional but helpful):
  - `anchor_ts = time.time()` or use the webcam `write_frame(...)` timestamp.
  - For fast sensors, call `add_data` immediately.
  - For slow sensors, run in a background thread and set their `data['timestamp'] = anchor_ts` before calling `add_data`.

## Why Not Full Async?

- You don’t strictly need `asyncio` for synchronization. The key is timestamped buffering and a tolerance window. Threads are adequate for offloading slow capture (you already use a thread for expression).
- If you plan to scale to more sensors or heavy models, `asyncio` or `concurrent.futures.ThreadPoolExecutor` can help avoid blocking, but synchronization is still best handled by a timestamp-based aggregator like this.

## Where To Adjust

- Update `DataCoordinator` construction to tune alignment to your hardware:
  - `coordinator = DataCoordinator(output_builder, max_skew_ms=50, max_wait_ms=200)`
  - Optionally set `required_sources` if you’re not capturing fNIRS every run:
    - `coordinator = DataCoordinator(output_builder, required_sources={'emg','hand','expression','robot'})`

---

This change ensures a row such as `1762144897.237082,2025-11-03T04:41:37.237Z` is used as the anchor for all fields, and delayed sources are merged into that same row within the configured tolerance.