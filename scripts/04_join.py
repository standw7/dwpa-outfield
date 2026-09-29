"""Join plays and win probability into data/events.parquet."""
import pandas as pd

from common import DATA

plays = pd.read_parquet(DATA / "plays.parquet")
winprob = pd.read_parquet(DATA / "winprob.parquet")

# a handful of plays have no win probability, those get dropped
events = plays.merge(winprob, on="play_id", how="inner")
events.to_parquet(DATA / "events.parquet", index=False)

print(f"{len(events)} plays x {events.shape[1]} columns "
      f"({len(plays) - len(events)} without win probability)")
print(f"{events.player_id.nunique()} outfielders, {events.game_pk.nunique()} games")
print(events.groupby("season").size().rename("plays").to_string())
