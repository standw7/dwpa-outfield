"""Get every outfielder for each season from the Savant OAA and outfield jump leaderboards."""
import io

import pandas as pd

from common import DATA, SEASONS, get

URL = "https://baseballsavant.mlb.com/leaderboard/"


def leaderboard(name, params):
    """Download a leaderboard CSV for each season and stack them."""
    tables = []
    for year in SEASONS:
        r = get(URL + name, {**params, "csv": "true", "year": year,
                             "startYear": year, "endYear": year})
        t = pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")))
        t["season"] = year
        tables.append(t)
    return pd.concat(tables, ignore_index=True)


oaa = leaderboard("outs_above_average", {"type": "Fielder", "pos": "of", "min": 1})
oaa = oaa.rename(columns={"last_name, first_name": "name", "display_team_name": "team",
                          "primary_pos_formatted": "pos", "outs_above_average": "oaa",
                          "fielding_runs_prevented": "frp"})
oaa = oaa[["player_id", "season", "name", "team", "pos", "oaa", "frp"]]

jump = leaderboard("outfield_jump", {"min": 1})
jump = jump.rename(columns={"resp_fielder_id": "player_id",
                            "rel_league_reaction_distance": "jump_reaction_ft",
                            "rel_league_burst_distance": "jump_burst_ft",
                            "rel_league_routing_distance": "jump_route_ft",
                            "rel_league_bootup_distance": "jump_total_ft"})
jump = jump[["player_id", "season", "jump_reaction_ft", "jump_burst_ft",
             "jump_route_ft", "jump_total_ft"]]

# not everyone has jump data so use a left join
players = oaa.merge(jump, on=["player_id", "season"], how="left")
DATA.mkdir(exist_ok=True)
players.to_parquet(DATA / "players.parquet", index=False)
print(f"{len(players)} player-seasons, {players.player_id.nunique()} players")
