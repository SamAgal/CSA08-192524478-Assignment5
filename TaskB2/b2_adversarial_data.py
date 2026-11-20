

import csv
import io
import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

readings = [
    ("Adyar", "2026-10-01", 48.0),
    ("Guindy", "2026-10-01", 95.0),
    ("Guindy", "2026-10-03", 121.0),
    ("Adyar", "2026-10-04", 60.0),
]

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
# TODO 1: Insert all readings with ONE executemany call using ? placeholders, then commit
con.executemany("INSERT INTO aq (station, day, pm25) VALUES (?, ?, ?)", readings)
con.commit()


def station_average(name):
    # TODO 2: Return the average pm25 of the given station using a parameterised SELECT ... WHERE station = ?
    cur = con.execute("SELECT AVG(pm25) FROM aq WHERE station = ?", (name,))
    row = cur.fetchone()
    return row[0] if row else None


def test_adversarial_files():
    cases = {
        "missing_column": "station,date\nAdyar,2026-10-01\n",
        "wrong_delimiter": "station;date;pm25\nAdyar;2026-10-01;48.0\n",
        "empty_file": "",
    }
    print("\n--- Adversarial File Ingestion Tests ---")
    for label, content in cases.items():
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames or []
        if set(headers) != {"station", "date", "pm25"}:
            print(f"[{label}] Rejected schema mismatch: headers={headers}")
        else:
            print(f"[{label}] Accepted rows: {list(reader)}")

    # Wrong encoding simulation (Latin-1 byte 0xb0 degree symbol read as UTF-8)
    bad_bytes = "station,date,pm25\nAdyar\xb0,2026-10-01,48.0\n".encode("latin-1")
    try:
        bad_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"[wrong_encoding] Caught UnicodeDecodeError safely: {e}")


def test_adversarial_sentiment():
    POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
    NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
    NEGATORS = {"not", "never", "no"}

    def score(text):
        words = text.lower().replace(",", "").replace(".", "").split()
        total = 0
        for i, w in enumerate(words):
            val = 1 if w in POSITIVE else (-1 if w in NEGATIVE else 0)
            if i > 0 and words[i - 1] in NEGATORS:
                val = -val
            total += val
        return total

    adversarial_texts = [
        ("Sarcasm", "Oh great, more thick black smoke, truly clean air!"),
        ("Double Negative", "The air quality is not bad at all."),
        ("Mixed Opinion", "The bus was fast and helpful, but the smoke is bad."),
    ]
    print("\n--- Adversarial Sentiment Tests ---")
    for kind, txt in adversarial_texts:
        s = score(txt)
        lbl = "positive" if s > 0 else ("negative" if s < 0 else "neutral")
        print(f"[{kind:15s}] Score={s:+d} | Label={lbl:8s} | Text='{txt}'")


def benchmark_insert_methods(n=50_000):
    sample = [(f"Stn_{i%12}", "2026-10-01", float(i % 150)) for i in range(n)]

    c1 = sqlite3.connect(":memory:")
    c1.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
    t0 = time.perf_counter()
    c1.executemany("INSERT INTO aq VALUES (?, ?, ?)", sample)
    c1.commit()
    t_many = time.perf_counter() - t0
    c1.close()

    c2 = sqlite3.connect(":memory:")
    c2.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
    t0 = time.perf_counter()
    for row in sample:
        c2.execute("INSERT INTO aq VALUES (?, ?, ?)", row)
    c2.commit()
    t_loop = time.perf_counter() - t0
    c2.close()

    print(f"\n--- Insert Benchmark ({n} rows) ---")
    print(f"executemany(): {t_many:.4f}s | execute() in loop: {t_loop:.4f}s")


if __name__ == "__main__":
    print(station_average("Adyar"), station_average("Guindy"))
    print(station_average("Adyar' OR '1'='1"))
    con.close()
    test_adversarial_files()
    test_adversarial_sentiment()
    benchmark_insert_methods()
