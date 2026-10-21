# Smart Water Intelligence — Day 1

Day 1 includes a Python rule-based detector and simulated water readings.

## Important scope note
This is a software prototype using simulated readings. It does not detect actual physical leaks without sensor data. The rules are demo thresholds, not validated engineering thresholds.

## Requirements
- Python 3.10+
- pip

## Run the scenarios
```bash
python simulator.py
```

## Run tests
```bash
python -m unittest -v
```

## Day 1 scenarios
- Normal usage
- Continuous flow (possible leak)
- Tank overflow risk
- Unusual consumption

## Next
Day 2 adds a Streamlit dashboard and SQLite persistence.
