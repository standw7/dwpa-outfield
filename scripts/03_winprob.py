"""Get win probability for each play from the MLB Stats API, one request per game.

Savant play_id matches the pitch playId in the MLB data, so we only keep those pitches.
"""
import json
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from tqdm import tqdm

from common import DATA, RAW, get

URL = "https://statsapi.mlb.com/api/v1/game/{}/winProbability"
# only request the fields we need
FIELDS = "about,atBatIndex,halfInning,result,eventType,playEvents,playId," \
         "homeTeamWinProbability,homeTeamWinProbabilityAdded"
CACHE = RAW / "wp"


def fetch(game_pk, play_ids):
    """WP rows for our plays in one game (cached)."""
    path = CACHE / f"{game_pk}.json"
    if not path.exists():
        rows = [{"play_id": pitch["playId"],
                 "half_inning": pa["about"]["halfInning"],
                 "event": pa["result"].get("eventType"),
                 "home_wp_after": pa.get("homeTeamWinProbability"),
                 "home_wp_added": pa.get("homeTeamWinProbabilityAdded")}
                for pa in get(URL.format(game_pk), {"fields": FIELDS}).json()
                for pitch in pa.get("playEvents", [])
                if pitch.get("playId") in play_ids]
        path.write_text(json.dumps(rows))
    return json.loads(path.read_text())


CACHE.mkdir(parents=True, exist_ok=True)
by_game = pd.read_parquet(DATA / "plays.parquet").groupby("game_pk").play_id.apply(set)
with ThreadPoolExecutor(8) as pool:
    results = list(tqdm(pool.map(fetch, by_game.index, by_game), total=len(by_game)))

winprob = pd.DataFrame([row for rows in results for row in rows])
winprob.to_parquet(DATA / "winprob.parquet", index=False)
print(f"{len(winprob)} of {by_game.map(len).sum()} plays matched")
