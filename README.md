# CSA08 - Python Programming: Assignment 5
**Title:** Data Acquisition, Cleaning, Analysis, Profiling & Introductory AI Applications  
**Name:** J. Sam Agal  
**Register Number:** 192524478  
**Course:** CSA08 - Python Programming (CO5 Coverage)  
**Python Version:** Python 3.12  
**Libraries Used:** Python Standard Library (`csv`, `io`, `sqlite3`, `statistics`, `re`, `time`, `timeit`, `cProfile`, `pstats`, `pathlib`, `random`) + Third-Party (`pandas`, `matplotlib`) — see `requirements.txt`

## Repository Structure & Execution Commands
All scripts resolve input/output paths automatically using `Path(__file__).resolve().parent`, so you can run them from the repository root OR inside each task directory:
```bash
python TaskA/part_a_design_verification.py
python TaskB1/b1_cleaning_pipeline.py
python TaskB2/b2_adversarial_data.py
python TaskB3/b3_loops_vs_libraries_vs_sql.py
python TaskB4/b4_final_engineering_decision.py
```

## Summary of Task Results
- **Part A (Tasks A1–A5):** Complete algorithmic pseudocode (SIMATS Engineering Standard), SQLite DDL schema (`stations`, `readings` with composite PK and `CHECK` constraints), cleaning & normalization formulas (Min-Max & Z-Score), chart selection justification, debugging/profiling plans, and lexicon-based sentiment + extractive summarizer + rule-based chatbot designs with Big-O complexity analyses.
- **Task B1 (Cleaning & Visualisation Pipeline):** Implemented `load_clean()` and `min_max()` (including `pm25 > 999` outlier filtering), loaded cleaned station telemetry into SQLite using `executemany`, answered the 3 board analytical queries via SQL, generated 4 high-resolution matplotlib charts (`pm25_trend.png`, `station_comparison.png`, `temp_vs_pm25.png`, `worst_hours.png`), and benchmarked Python loops vs. Pandas across 1K, 100K, and 1M rows.
- **Task B2 (Adversarial Data Engineering):** Stress-tested ingestion against missing columns, wrong delimiters, Latin-1/UTF-16 encoding mismatches, and empty files; verified SQLite parameterized `?` queries against SQL injection (`Adyar' OR '1'='1`), benchmarked `executemany` vs. `execute` in a loop, and tested sentiment edge cases (sarcasm, double negatives, mixed opinions).
- **Task B3 (Loops vs. Libraries vs. SQL):** Verified numerical equivalence across plain Python `csv` loops, `pandas.groupby`, and SQLite `GROUP BY`; benchmarked scaling across 1, 12, and 120 stations (up to 1,051,200 rows) and profiled bottlenecks with `cProfile`.
- **Task B4 (Final Engineering Decision):** Evaluated the lexicon sentiment scorer and extractive summarizer on 50 citizen complaints (achieving 82% human-label agreement), measured SQLite composite index `(station, day)` speedup, and formulated an evidence-based production architecture for 112 stations at 15-minute intervals (~3.92M rows/year) and 50,000 monthly complaints.
