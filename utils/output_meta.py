"""Functions to build out the output directory for the data capture along with the corresponding meta data and participant info"""

import pathlib

class OutputBuilder:
    def __init__(self, output_dir, save_dir, identity):
        self.output_dir = pathlib.Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.save_dir = self.output_dir / pathlib.Path(save_dir)
        
        self.csv_path = self.save_dir / f"{pathlib.Path(identity)}.csv" 

    def make_directory(self):
        self.save_dir.mkdir(exist_ok=False) 
    
    def make_csv(self):
        if self.csv_path.exists():
            raise FileExistsError(f"File already exists: {self.csv_path}")
        else:
            self.csv_path.touch()

def test():
    build = OutputBuilder("output", "run1", "experiment1")
    build.make_directory()
    build.make_csv()

if __name__ == "__main__":
    test()