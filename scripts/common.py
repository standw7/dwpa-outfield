"""Paths, seasons, and a download helper with retries."""
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
SEASONS = range(2016, 2026)  # savant range data starts in 2016

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0"


def get(url, params=None, tries=5):
    """GET with retries (backs off 1s, 2s, 4s, ...)."""
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r
            if r.status_code not in (429, 500, 502, 503, 504):
                r.raise_for_status()
        except requests.RequestException:
            if attempt == tries - 1:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to download {url} {params}")
