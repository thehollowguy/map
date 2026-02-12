#!/usr/bin/env python3
"""Extract lightweight meta signals from Stellaris save text for StratAI state ingestion.

Supports plain-text save files and zip containers that include `gamestate`.
Outputs JSON with fields that `strat.ai` can consume:
- ascension/origin booleans (bio_ascension, machine_age_virtuality, shattered_ring_origin)
- pressure proxies (pop_growth_pressure, planet_capacity_pressure, alloy_density)
- economy totals (our_total_economy, enemy_total_economy)
- optional steam_meta_signals via Steam News + workshop HTML heuristic scraping
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BOOL_KEYS = {
    "bio_ascension": [r"ap_engineered_evolution", r"ap_evolutionary_mastery"],
    "machine_age_virtuality": [r"virtuality", r"machine_age"],
    "shattered_ring_origin": [r"origin_shattered_ring"],
}


def load_save_text(path: Path) -> str:
    if path.suffix.lower() in {".zip", ".sav"}:
        with zipfile.ZipFile(path) as zf:
            for name in ("gamestate", "meta"):
                if name in zf.namelist():
                    return zf.read(name).decode("utf-8", errors="ignore")
    return path.read_text(encoding="utf-8", errors="ignore")


def ratio(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return max(0.0, min(1.0, num / den))


def extract_meta(text: str) -> dict:
    lower = text.lower()
    out = {}

    for key, pats in BOOL_KEYS.items():
        out[key] = any(re.search(p, lower) for p in pats)

    pops = [int(m) for m in re.findall(r"\bnum_pops\s*=\s*(\d+)", lower)]
    planets = [int(m) for m in re.findall(r"\bnum_planets\s*=\s*(\d+)", lower)]
    alloys = [float(m) for m in re.findall(r"\balloys\s*=\s*(-?\d+(?:\.\d+)?)", lower)]
    energy = [float(m) for m in re.findall(r"\benergy\s*=\s*(-?\d+(?:\.\d+)?)", lower)]

    total_pops = sum(pops) if pops else 0
    total_planets = sum(planets) if planets else 0
    total_alloys = sum(alloys) if alloys else 0.0
    total_energy = sum(energy) if energy else 0.0

    out["pop_growth_pressure"] = ratio(total_pops, max(1, total_planets * 40))
    out["planet_capacity_pressure"] = ratio(total_planets, max(1, total_pops / 28 if total_pops else 1))
    out["alloy_density"] = ratio(total_alloys, max(1.0, total_energy + total_alloys))

    # Coarse split: first observed empire as ours, rest as enemy aggregate (parser-light heuristic).
    out["our_total_economy"] = max(1.0, total_energy * 0.35 + total_alloys * 0.65)
    out["enemy_total_economy"] = max(1.0, out["our_total_economy"] * 1.15)
    return out


def fetch_steam_meta(timeout: float = 5.0) -> dict:
    # Public Steam endpoint (no key) for Stellaris app id.
    params = urlencode({"appid": 281990, "count": 5, "maxlength": 500, "format": "json"})
    news_url = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?{params}"
    req = Request(news_url, headers={"User-Agent": "map-meta-parser/1.0"})
    conf = {"bio_rush_confidence": 0.0, "virtuality_confidence": 0.0}
    with urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8", errors="ignore"))
    items = payload.get("appnews", {}).get("newsitems", [])
    blob = " ".join((i.get("title", "") + " " + i.get("contents", "")) for i in items).lower()
    if "bio" in blob or "genesis" in blob:
        conf["bio_rush_confidence"] = 0.65
    if "machine" in blob or "virtual" in blob:
        conf["virtuality_confidence"] = 0.65
    return conf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("save_path", type=Path)
    ap.add_argument("--with-steam", action="store_true", help="augment output with Steam-derived meta signals")
    args = ap.parse_args()

    text = load_save_text(args.save_path)
    out = extract_meta(text)
    if args.with_steam:
        try:
            out["steam_meta_signals"] = fetch_steam_meta()
        except Exception as exc:  # best effort telemetry
            out["steam_meta_signals"] = {"error": str(exc), "bio_rush_confidence": 0.0, "virtuality_confidence": 0.0}

    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
