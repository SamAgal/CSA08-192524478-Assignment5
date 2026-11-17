"""Part A (A1-A5): Reference implementation verifying Part A designs, SQLite DDL, and AI prototypes."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def verify_schema():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.executescript("""
        CREATE TABLE stations (
            station_id TEXT PRIMARY KEY,
            station_name TEXT NOT NULL UNIQUE,
            zone TEXT NOT NULL,
            temp_unit TEXT CHECK (temp_unit IN ('C', 'F')) DEFAULT 'C'
        );
        CREATE TABLE readings (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT NOT NULL,
            reading_date TEXT NOT NULL,
            reading_hour INTEGER NOT NULL CHECK (reading_hour BETWEEN 0 AND 23),
            pm25 REAL CHECK (pm25 >= 0 AND pm25 <= 999),
            pm10 REAL CHECK (pm10 >= 0 AND pm10 <= 1500),
            no2 REAL CHECK (no2 >= 0 AND no2 <= 500),
            temp_c REAL CHECK (temp_c BETWEEN -10 AND 60),
            UNIQUE(station_id, reading_date, reading_hour),
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        );
        CREATE INDEX idx_readings_station_date ON readings(station_id, reading_date);
    """)
    cur.execute("INSERT INTO stations VALUES ('STN01', 'Adyar', 'South', 'C');")
    cur.execute("INSERT INTO readings(station_id, reading_date, reading_hour, pm25, pm10, no2, temp_c) VALUES ('STN01', '2026-10-15', 9, 48.5, 82.0, 31.2, 31.4);")
    conn.commit()
    row = cur.execute("SELECT station_id, reading_date, pm25 FROM readings").fetchone()
    conn.close()
    print("[Part A Schema Verified]", row)


def rule_chatbot(query, latest_pm25):
    q = query.lower()
    for stn, val in latest_pm25.items():
        if stn.lower() in q and "pm2.5" in q.replace("pm25", "pm2.5"):
            status = "Good" if val <= 30 else ("Moderate" if val <= 60 else "Poor")
            return f"Latest PM2.5 in {stn}: {val:.1f} ug/m3 ({status})."
    return "Sorry, specify a valid Chennai station (Adyar, Guindy, Velachery, Anna Nagar) and metric (PM2.5)."


if __name__ == "__main__":
    verify_schema()
    print("[Part A Chatbot Test]", rule_chatbot("What is the PM2.5 in Adyar today?", {"Adyar": 48.5, "Guindy": 95.0}))
