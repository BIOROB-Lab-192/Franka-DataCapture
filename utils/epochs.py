import CSV_writer

class EpochWriter(CSV_writer.CSVWRiter):
    def __init__(self, filepath, fields):
        super().__init__(filepath, fields)

    def mark_epoch(self, epoch_id, start_time, end_time, label):
        self.write_row({
            "epoch_id": epoch_id,
            "start_time": start_time,
            "end_time": end_time,
            "label": label or ""
        })
        #  send epoch signal to fNIRS