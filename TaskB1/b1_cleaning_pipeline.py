

import csv
import io
import random
import sqlite3
import time
import tracemalloc
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
Guindy,2026-10-04,1200
"""


def load_clean(text):
    """Returns (station, date, pm25) tuples for valid, non-negative readings <= 999 only."""
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        val_str = (row.get("pm25") or "").strip()
        if not val_str or val_str.upper() == "NA":
            continue
        try:
            pm = float(val_str)
        except ValueError:
            continue
        if pm < 0 or pm > 999:
            continue
        rows.append((row["station"].strip(), row["date"].strip(), pm))
    return rows


def min_max(values):
    """Scale each value to the range 0-1 using (v - min) / (max - min), rounded to 3 decimals."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [0.0 for _ in values]
    return [round((v - lo) / (hi - lo), 3) for v in values]


def clean_full_csv(csv_path):
    """B1.1: Full cleaning pipeline on multi-column station file (dedup, F->C, range checks)."""
    seen = set()
    cleaned = []
    before_rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            before_rows.append(dict(r))
            key = (r["station"].strip(), r["date"].strip(), int(r["hour"]))
            if key in seen:
                continue
            pm_str = (r["pm25"] or "").strip()
            if not pm_str or pm_str.upper() == "NA":
                continue
            pm = float(pm_str)
            if pm < 0 or pm > 999:
                continue
            temp = float(r["temperature"])
            if r["unit"].strip().upper() == "F":
                temp = round((temp - 32.0) * 5.0 / 9.0, 2)
            seen.add(key)
            cleaned.append((
                r["station"].strip(),
                r["date"].strip(),
                int(r["hour"]),
                pm,
                float(r["pm10"]),
                float(r["no2"]),
                temp,
            ))
    return before_rows, cleaned


def store_and_query_sqlite(cleaned_rows, db_path):
    """B1.3: Load cleaned rows into SQLite using executemany and answer 3 board questions."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE readings (
            station TEXT,
            reading_date TEXT,
            reading_hour INTEGER,
            pm25 REAL,
            pm10 REAL,
            no2 REAL,
            temp_c REAL,
            PRIMARY KEY (station, reading_date, reading_hour)
        )
    """)
    cur.executemany("INSERT INTO readings VALUES (?, ?, ?, ?, ?, ?, ?)", cleaned_rows)
    conn.commit()

    q1 = cur.execute("SELECT ROUND(AVG(pm25), 2) FROM readings WHERE station = 'Adyar' AND reading_date LIKE '2026-10-%'").fetchone()[0]
    q2 = cur.execute("SELECT station, ROUND(AVG(pm25), 2) AS avg_pm25 FROM readings GROUP BY station ORDER BY avg_pm25 DESC").fetchall()
    q3 = cur.execute("SELECT reading_hour, ROUND(AVG(pm25), 2) AS avg_pm25 FROM readings GROUP BY reading_hour ORDER BY avg_pm25 DESC LIMIT 3").fetchall()
    conn.close()
    return q1, q2, q3


def generate_charts(cleaned_rows):
    """B1.4: Generate 4 charts designed in A3.1."""
    df = pd.DataFrame(cleaned_rows, columns=["station", "date", "hour", "pm25", "pm10", "no2", "temp_c"])

    # 1. Line chart: PM2.5 trend over October
    plt.figure(figsize=(7, 4))
    for stn, grp in df.groupby("station"):
        grp_sorted = grp.sort_values("date")
        plt.plot(grp_sorted["date"], grp_sorted["pm25"], marker="o", label=stn)
    plt.title("October PM2.5 Trend by Station")
    plt.xlabel("Date")
    plt.ylabel("PM2.5 (ug/m3)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(BASE_DIR / "chart1_pm25_trend.png", dpi=150)
    plt.close()

    # 2. Bar chart: Comparison of stations (mean PM2.5)
    plt.figure(figsize=(6, 4))
    stn_means = df.groupby("station")["pm25"].mean().sort_values(ascending=False)
    plt.bar(stn_means.index, stn_means.values, color=["#222222", "#666666", "#999999"])
    plt.title("Mean PM2.5 Comparison Across Stations")
    plt.xlabel("Station")
    plt.ylabel("Mean PM2.5 (ug/m3)")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "chart2_station_comparison.png", dpi=150)
    plt.close()

    # 3. Scatter plot: Temperature vs PM2.5
    plt.figure(figsize=(6, 4))
    plt.scatter(df["temp_c"], df["pm25"], color="#111111", s=60, alpha=0.8)
    plt.title("Relationship Between Temperature (C) and PM2.5")
    plt.xlabel("Temperature (C)")
    plt.ylabel("PM2.5 (ug/m3)")
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(BASE_DIR / "chart3_temp_vs_pm25.png", dpi=150)
    plt.close()

    # 4. Bar chart: Hours with worst air quality
    plt.figure(figsize=(6, 4))
    hr_means = df.groupby("hour")["pm25"].mean().sort_index()
    plt.bar([f"{h:02d}:00" for h in hr_means.index], hr_means.values, color="#444444")
    plt.title("Mean PM2.5 by Hour of Day")
    plt.xlabel("Hour of Day")
    plt.ylabel("Mean PM2.5 (ug/m3)")
    plt.tight_layout()
    plt.savefig(BASE_DIR / "chart4_worst_hours.png", dpi=150)
    plt.close()


def benchmark_loops_vs_pandas():
    """Alternative Concept & Complexity Analysis: 1K, 100K, 1M rows."""
    results = []
    stations = ["Adyar", "Guindy", "Velachery", "Anna Nagar"]
    for n in [1_000, 100_000, 1_000_000]:
        buf = io.StringIO()
        buf.write("station,date,pm25\n")
        for i in range(n):
            val = "NA" if i % 20 == 0 else ("-5" if i % 33 == 0 else f"{random.uniform(20, 180):.1f}")
            buf.write(f"{stations[i % 4]},2026-10-{(i % 30)+1:02d},{val}\n")
        raw_str = buf.getvalue()

        # Python csv + loops
        tracemalloc.start()
        t0 = time.perf_counter()
        cleaned = load_clean(raw_str)
        _ = min_max([r[2] for r in cleaned])
        t_loop = time.perf_counter() - t0
        _, peak_loop = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Pandas vectorized
        tracemalloc.start()
        t0 = time.perf_counter()
        df = pd.read_csv(io.StringIO(raw_str), na_values=["NA", ""])
        df = df.dropna(subset=["pm25"])
        df = df[(df["pm25"] >= 0) & (df["pm25"] <= 999)]
        lo, hi = df["pm25"].min(), df["pm25"].max()
        df["norm"] = ((df["pm25"] - lo) / (hi - lo)).round(3)
        t_pd = time.perf_counter() - t0
        _, peak_pd = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results.append((n, round(t_loop, 4), round(peak_loop / (1024 * 1024), 2), round(t_pd, 4), round(peak_pd / (1024 * 1024), 2)))
    return results


if __name__ == "__main__":
    # Complete the Code verification
    clean = load_clean(RAW)
    print("Complete the Code clean rows:", clean)
    print("Complete the Code min_max   :", min_max([pm for _, _, pm in clean]))

    # B1.1, B1.3, B1.4
    before, after = clean_full_csv(BASE_DIR / "sample_raw_air_quality.csv")
    print(f"\nB1.1 Before count: {len(before)} | After count: {len(after)}")
    q1, q2, q3 = store_and_query_sqlite(after, BASE_DIR / "air_quality.db")
    print(f"B1.3 Q1 (Adyar Oct Mean): {q1}")
    print(f"B1.3 Q2 (Station Ranking): {q2}")
    print(f"B1.3 Q3 (Worst Hours)    : {q3}")
    generate_charts(after)
    print("B1.4 Charts saved to TaskB1/*.png")

    print("\nB1 Benchmark (N, Loop_s, Loop_MB, Pandas_s, Pandas_MB):")
    for row in benchmark_loops_vs_pandas():
        print(" ", row)
