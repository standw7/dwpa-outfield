"""Compute dWPA for every outfield event in data/events.parquet."""
import sys

import numpy as np
import pandas as pd

from common import DATA


def calculate(events):
    """
    dWPA = Win Probability  * X

    X =
        For catch = 1 (success):
            [(1 - catch probability) * (distance traveled / opportunity time)]
        For catch = 0 (failure):
            [Catch probability * (distance traveled / opportunity time)]

    Win Probability is the win probability added by the play, from the
    fielding team's side (home team fields in the top half).
    """
    effort = events.distance_ft / events.opp_time_s
    x = np.where(events.caught == 1, 1 - events.catch_prob, events.catch_prob) * effort
    fielding_wpa = np.where(events.half_inning == "top", 1, -1) * events.home_wp_added
    return pd.DataFrame({"play_id": events.play_id, "dwpa": fielding_wpa * x})


if __name__ == "__main__":
    events = pd.read_parquet(DATA / "events.parquet")
    dwpa = calculate(events)
    out = sys.argv[1] if len(sys.argv) > 1 else DATA / "dwpa.csv"
    dwpa.to_csv(out, index=False)
    print(f"{len(dwpa)} events -> {out}")
    print(dwpa.head(20).to_string(index=False))
