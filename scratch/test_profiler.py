"""
Verification test for DataProfiler report generation.
"""

from pathlib import Path
from app.analytics.data_profiler import DataProfiler
from app.etl.extract.csv_loader import CSVLoader

def test_profiler_generation():
    loader = CSVLoader()
    raw_datasets = loader.load_all_raw_datasets()
    
    profiler = DataProfiler()
    paths = profiler.generate_batch_profiles(raw_datasets)
    print("Generated profile report paths:")
    for k, p in paths.items():
        print(f"  - {k}: {p}")

if __name__ == "__main__":
    test_profiler_generation()
