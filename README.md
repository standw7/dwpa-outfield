# dwpa-outfield

Scripts for pulling outfield play data (2016-2025) from Baseball Savant and win probability from the MLB Stats API.

    pip install pandas pyarrow requests tqdm
    cd scripts
    python 01_outfielders.py
    python 02_plays.py
    python 03_winprob.py
    python 04_join.py

Output goes in data/. events.parquet is the main table (one row per play). Downloads are cached in data/raw so you can rerun if something stops. Steps 2 and 3 take about 10 min each.

Win probability columns are from the home team's point of view.
