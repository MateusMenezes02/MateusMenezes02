#!/usr/bin/env python3
"""Render compact, self-contained light and dark contribution heatmaps."""
from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contributions.json"
ASSETS = ROOT / "assets"

THEMES = {
    "dark": {"bg": "#0d1117", "text": "#e6edf3", "muted": "#8b949e", "empty": "#21262d", "levels": ["#164c5b", "#126f86", "#00a8c6", "#51d3e8"]},
    "light": {"bg": "#ffffff", "text": "#24292f", "muted": "#57606a", "empty": "#eaeef2", "levels": ["#b6e3eb", "#70cad9", "#209bb5", "#087f9d"]},
}


def svg_for(payload: dict, theme_name: str) -> str:
    t = THEMES[theme_name]
    day_map = {d["date"]: d for d in payload.get("days", [])}
    dates = sorted(day_map)
    if not dates:
        raise ValueError("contributions.json has no days")
    end = date.fromisoformat(dates[-1])
    start = end - timedelta(days=370)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # Sunday-aligned calendar
    cells = []
    for week in range(53):
        for row in range(7):
            current = start + timedelta(days=week * 7 + row)
            item = day_map.get(current.isoformat())
            level = int(item["level"]) if item else 0
            color = t["empty"] if level == 0 else t["levels"][level - 1]
            x, y = 44 + week * 15, 42 + row * 15
            title = f'{item["count"] if item else 0} contributions on {current.isoformat()}'
            delay = (week + row) * 0.008
            cells.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{color}" opacity="0"><title>{escape(title)}</title><animate attributeName="opacity" from="0" to="1" dur=".18s" begin="{delay:.3f}s" fill="freeze"/></rect>')
    stats = payload["stats"]
    best = stats.get("best_day") or {"date": "—", "count": 0}
    legend = ''.join(f'<rect x="{705+i*15}" y="167" width="11" height="11" rx="2" fill="{c}"/>' for i, c in enumerate([t["empty"], *t["levels"]]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="210" viewBox="0 0 860 210" role="img" aria-labelledby="title desc">
<title id="title">GitHub contribution activity</title><desc id="desc">{stats["total"]:,} contributions in the last year; current streak {stats["current_streak"]} days.</desc>
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}} .m{{fill:{t["muted"]};font-size:10px}} .s{{fill:{t["text"]};font-size:12px;font-weight:600}}</style>
<rect width="860" height="210" rx="12" fill="{t["bg"]}"/><text x="20" y="25" class="s">CONTRIBUTION ACTIVITY</text><text x="20" y="193" class="m">{stats["total"]:,} contributions in the last year  ·  current streak: {stats["current_streak"]} days  ·  longest: {stats["longest_streak"]} days  ·  best: {best["count"]} on {best["date"]}</text>
<text x="20" y="51" class="m">Sun</text><text x="20" y="81" class="m">Tue</text><text x="20" y="111" class="m">Thu</text>{''.join(cells)}<text x="675" y="176" class="m">Less</text>{legend}<text x="785" y="176" class="m">More</text></svg>'''


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)
    for name in THEMES:
        (ASSETS / f"heatmap-v2-{name}.svg").write_text(svg_for(payload, name), encoding="utf-8")


if __name__ == "__main__":
    main()
