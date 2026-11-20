

import cProfile
import csv
import io
import pstats
import random
import sqlite3
import statistics
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent


def generate_dataset(num_stations, days=365, hours_per_day=24):
    """Generates (station, day, pm25) rows (~8,760 rows per station per year)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["station", "day", "pm25"])
    rng = random.Random(42)
    for s in range(1, num_stations + 1):
        stn = f"STN_{s:03d}"
        for d in range(1, days + 1):
            day_str = f"2026-{(d % 12) + 1:02d}-{(d % 28) + 1:02d}"
            for _ in range(hours_per_day):
                writer.writerow([stn, day_str, round(rng.uniform(15.0, 160.0), 2)])
    return buf.getvalue()


def method_python_loops(csv_text):
    grouped = defaultdict(list)
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        grouped[(row["station"], row["day"])].append(float(row["pm25"]))
    return {k: round(statistics.mean(v), 4) for k, v in grouped.items()}


def method_python_one_pass(csv_text):
    """Alternative Concept: O(stations * days) memory using running sum & count."""
    acc = {}
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        key = (row["station"], row["day"])
        if key not in acc:
            acc[key] = [0.0, 0]
        acc[key][0] += float(row["pm25"])
        acc[key][1] += 1
    return {k: round(s / c, 4) for k, (s, c) in acc.items()}


def method_pandas(csv_text):
    df = pd.read_csv(io.StringIO(csv_text))
    res = df.groupby(["station", "day"])["pm25"].mean().round(4)
    return res.to_dict()


def method_sqlite(csv_text):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
    reader = csv.DictReader(io.StringIO(csv_text))
    conn.executemany("INSERT INTO aq VALUES (?, ?, ?)", ((r["station"], r["day"], float(r["pm25"])) for r in reader))
    conn.commit()
    rows = conn.execute("SELECT station, day, ROUND(AVG(pm25), 4) FROM aq GROUP BY station, day").fetchall()
    conn.close()
    return {(r[0], r[1]): r[2] for r in rows}


if __name__ == "__main__":
    # B3.1: Verify exact agreement on small data
    small_csv = generate_dataset(num_stations=2, days=5, hours_per_day=24)
    r_loop = method_python_loops(small_csv)
    r_one = method_python_one_pass(small_csv)
    r_pd = method_pandas(small_csv)
    r_sql = method_sqlite(small_csv)
    assert r_loop == r_one == r_pd == r_sql, "Mismatch across methods!"
    print("B3.1 Verification: All 4 methods agree 100% on small dataset.")

    # B3.2: Scaling across 1, 12, and 120 stations (~8,760, 105,120, 1,051,200 rows)
    print("\nB3.2 Scaling Comparison (Stations, Rows, Loops_s, OnePass_s, Pandas_s, SQLite_s):")
    for stn_count in [1, 12, 120]:
        data_csv = generate_dataset(num_stations=stn_count, days=365, hours_per_day=24)
        row_count = stn_count * 365 * 24

        t0 = time.perf_counter()
        method_python_loops(data_csv)
        t_loop = time.perf_counter() - t0

        t0 = time.perf_counter()
        method_python_one_pass(data_csv)
        t_one = time.perf_counter() - t0

        t0 = time.perf_counter()
        method_pandas(data_csv)
        t_pd = time.perf_counter() - t0

        t0 = time.perf_counter()
        method_sqlite(data_csv)
        t_sql = time.perf_counter() - t0

        print(f"  Stations={stn_count:3d} | Rows={row_count:7d} | Loops={t_loop:.4f}s | OnePass={t_one:.4f}s | Pandas={t_pd:.4f}s | SQLite={t_sql:.4f}s")

    # B3.3: Profile plain-Python version with cProfile on 12 stations
    print("\nB3.3 cProfile Top Functions (12 stations / 105,120 rows):")
    med_csv = generate_dataset(num_stations=12, days=365, hours_per_day=24)
    profiler = cProfile.Profile()
    profiler.enable()
    method_python_loops(med_csv)
    profiler.disable()
    s_io = io.StringIO()
    ps = pstats.Stats(profiler, stream=s_io).sort_stats("tottime")
    ps.print_stats(8)
    print(s_io.getvalue())
