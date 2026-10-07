#!/usr/bin/env python3
"""Fetch a public GitHub contribution calendar and save verified local data."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "contributions.json"
URL = "https://github.com/users/{username}/contributions"
DEFAULT_USERNAME = "MateusMenezes02"


def parse_contributions(html: str) -> list[dict[str, object]]:
    """Parse GitHub calendar day cells, failing loudly on an unexpected page."""
    soup = BeautifulSoup(html, "html.parser")
    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        raise ValueError("No contribution calendar cells found; GitHub HTML may have changed.")
    tooltip_text = {
        tooltip.get("for"): tooltip.get_text(" ", strip=True)
        for tooltip in soup.select("tool-tip[for]")
        if tooltip.get("for")
    }
    days: list[dict[str, object]] = []
    for cell in cells:
        raw_date = cell.get("data-date")
        raw_count = cell.get("data-level")
        if not raw_date or raw_count is None:
            raise ValueError("Contribution calendar contains an incomplete day cell.")
        # GitHub provides exact totals in an associated screen-reader tooltip.
        cell_id = cell.get("id")
        label = tooltip_text.get(cell_id, cell.get("aria-label", ""))
        if not label:
            raise ValueError(f"No accessible contribution total for {raw_date}; GitHub HTML may have changed.")
        match = re.search(r"(\d+) contributions?", label)
        count = int(match.group(1)) if match else 0
        try:
            parsed = date.fromisoformat(raw_date)
            level = int(raw_count)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid calendar cell: {raw_date!r}, {raw_count!r}") from exc
        if not 0 <= level <= 4:
            raise ValueError(f"Unexpected contribution level {level}.")
        days.append({"date": parsed.isoformat(), "count": count, "level": level})
    if len(days) < 350:
        raise ValueError(f"Only {len(days)} calendar days were parsed; refusing incomplete data.")
    return days


def calculate_stats(days: list[dict[str, object]]) -> dict[str, object]:
    ordered = sorted(days, key=lambda d: str(d["date"]))
    total = sum(int(d["count"]) for d in ordered)
    best = max(ordered, key=lambda d: int(d["count"]), default=None)
    longest = current = running = 0
    for day in ordered:
        if int(day["count"]) > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    for day in reversed(ordered):
        if int(day["count"]) > 0:
            current += 1
        else:
            break
    monthly: dict[str, int] = {}
    for day in ordered:
        month = str(day["date"])[:7]
        monthly[month] = monthly.get(month, 0) + int(day["count"])
    return {"total": total, "current_streak": current, "longest_streak": longest,
            "best_day": best, "monthly_totals": monthly}


def main() -> int:
    username = os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME).strip()
    try:
        response = requests.get(URL.format(username=username), headers={"User-Agent": "profile-readme-updater/1.0"}, timeout=20)
        response.raise_for_status()
        days = parse_contributions(response.text)
        payload = {"username": username, "fetched_at": datetime.now().astimezone().isoformat(),
                   "days": days, "stats": calculate_stats(days)}
    except (requests.RequestException, ValueError) as exc:
        print(f"Error: could not update contributions: {exc}", file=sys.stderr)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(OUTPUT)
    print(f"Saved {len(days)} days for @{username} to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
