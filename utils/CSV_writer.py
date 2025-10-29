"""Functions to buffer and write the data captured from the differrent sensors"""

import csv

class CSVWRiter:
    def __init__(self, filepath, fields):
        self.filepath = filepath
        self.fields = fields

    def open_csv(self):
        self.file = open(self.filepath, mode='w', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
        self.writer.writeheader()

    def write_row(self, row):
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        self.file.close()
    