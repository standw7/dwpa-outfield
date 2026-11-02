"""Compute dWPA for every outfield event in data/events.parquet."""
import re
import sys

import numpy as np
import pandas as pd

from common import DATA, get

SAVANT_VIDEO = "https://baseballsavant.mlb.com/sporty-videos"
GAME_CONTENT = "https://statsapi.mlb.com/api/v1/game/{}/content"


def calculate(events):
    """
    dWPA = Win Probability  * X

    X =
        For catch = 1 (success):
            [(1 - catch probability) * (distance traveled / opportunity time)]
        For catch = 0 (failure):
            [Catch probability * (distance traveled / opportunity time)]

    Win Probability is the win probability added by the play, from the
    fielding team's side (home team fields in the top half), as a fraction
    of a win rather than percentage points.
    """
    effort = events.distance_ft / events.opp_time_s
    x = np.where(events.caught == 1, 1 - events.catch_prob, events.catch_prob) * effort
    fielding_wpa = np.where(events.half_inning == "top", 1, -1) * events.home_wp_added / 100
    return pd.DataFrame({"play_id": events.play_id, "dwpa": fielding_wpa * x})


def highlight_mp4(game_pk, play_id):
    """Stats API highlight mp4 tagged with this play, or None (older games often have none)."""
    content = get(GAME_CONTENT.format(game_pk)).json()
    items = (content.get("highlights", {}).get("highlights") or {}).get("items", [])
    for item in items:
        tags = {k.get("value") for k in item.get("keywordsAll", [])}
        if item.get("guid") == play_id or play_id in tags:
            mp4s = [p["url"] for p in item.get("playbacks", []) if p["url"].endswith(".mp4")]
            return mp4s[0] if mp4s else None
    return None


def pair_video(events, dwpa, n=2):
    """The n highest and n lowest dWPA plays, each paired with its video.

    Savant's video page has a clip for every Statcast play_id; the Stats API
    highlight is added when the game has one tagged with the play.
    """
    ranked = events.merge(dwpa, on="play_id").sort_values("dwpa", ascending=False)
    plays = pd.concat([ranked.head(n), ranked.tail(n)])

    rows = []
    for play in plays.itertuples():
        page = get(SAVANT_VIDEO, params={"playId": play.play_id})
        mp4 = re.search(r"https?://sporty-clips\.mlb\.com/[^\"' ]+\.mp4", page.text)
        title = re.search(r"<title>(.*?) \|", page.text, re.S)
        rows.append({
            "play_id": play.play_id,
            "name": play.name,
            "season": play.season,
            "dwpa": play.dwpa,
            "description": title.group(1).strip() if title else None,
            "video_page": page.url,
            "video_mp4": mp4.group(0) if mp4 else None,
            "highlight_mp4": highlight_mp4(play.game_pk, play.play_id),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    events = pd.read_parquet(DATA / "events.parquet")
    dwpa = calculate(events)
    out = sys.argv[1] if len(sys.argv) > 1 else DATA / "dwpa.csv"
    dwpa.to_csv(out, index=False)
    print(f"{len(dwpa)} events -> {out}")
    print(dwpa.head(20).to_string(index=False))

    videos = pair_video(events, dwpa)
    for v in videos.itertuples():
        print(f"\n{v.dwpa:+.1f}  {v.name} ({v.season}): {v.description}")
        print(f"  page:      {v.video_page}")
        print(f"  mp4:       {v.video_mp4}")
        print(f"  highlight: {v.highlight_mp4}")
