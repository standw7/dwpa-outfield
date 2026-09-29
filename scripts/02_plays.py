"""Download every ball hit to each outfielder (Savant range data), one request per player-season."""
import json
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from tqdm import tqdm

from common import DATA, RAW, get

URL = "https://baseballsavant.mlb.com/player-services/range"
CACHE = RAW / "range"


def fetch(player_id, season):
    """Plays for one player-season (cached)."""
    path = CACHE / f"{season}_{player_id}.json"
    if not path.exists():
        path.write_text(get(URL, {"playerId": player_id, "season": season}).text)
    return [dict(play, season=season) for play in json.loads(path.read_text())]


CACHE.mkdir(parents=True, exist_ok=True)
jobs = pd.read_parquet(DATA / "players.parquet")[["player_id", "season"]].drop_duplicates()
with ThreadPoolExecutor(4) as pool:
    results = list(tqdm(pool.map(fetch, jobs.player_id, jobs.season), total=len(jobs)))

plays = pd.DataFrame([p for batch in results for p in batch]).drop_duplicates("play_id")

# rename columns (the _10 ones are already in feet, just rounded to 10)
plays = plays.rename(columns={
    "name_display_first_last": "name",
    "catch_rate": "catch_prob", "distance": "distance_ft", "out": "caught",
    "opportunity_time": "opp_time_s", "sprint_speed": "sprint_speed_fps",
    "landing_pos_x_10": "land_x_ft", "landing_pos_y_10": "land_y_ft",
    "player_avg_norm_start_pos_x_10": "start_x_ft",   # average start spot for the season
    "player_avg_norm_start_pos_y_10": "start_y_ft"})
num = ["catch_prob", "distance_ft", "opp_time_s", "sprint_speed_fps"]
plays[num] = plays[num].apply(pd.to_numeric)  # these come in as strings

# pos: 7 = LF, 8 = CF, 9 = RF
plays.to_parquet(DATA / "plays.parquet", index=False)
print(f"{len(plays)} plays in {plays.game_pk.nunique()} games")
