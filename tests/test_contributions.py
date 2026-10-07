import importlib.util
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch", ROOT / "scripts" / "fetch_contributions.py")
fetch = importlib.util.module_from_spec(spec); spec.loader.exec_module(fetch)
render_spec = importlib.util.spec_from_file_location("render", ROOT / "scripts" / "render_heatmap_svg.py")
render = importlib.util.module_from_spec(render_spec); render_spec.loader.exec_module(render)


def days(counts):
    return [{"date": f"2026-01-{i + 1:02d}", "count": count, "level": min(count, 4)} for i, count in enumerate(counts)]


def test_stats_calculates_streaks_best_day_and_months():
    stats = fetch.calculate_stats(days([0, 2, 1, 0, 4, 5]))
    assert stats["total"] == 12
    assert stats["current_streak"] == 2
    assert stats["longest_streak"] == 2
    assert stats["best_day"] == {"date": "2026-01-06", "count": 5, "level": 4}
    assert stats["monthly_totals"] == {"2026-01": 12}


def test_parser_rejects_unexpected_html():
    try:
        fetch.parse_contributions("<html></html>")
    except ValueError as error:
        assert "No contribution calendar" in str(error)
    else:
        raise AssertionError("Parser accepted invalid markup")


def test_parser_uses_tooltip_totals():
    cells = "".join(f'<td class="ContributionCalendar-day" id="d{i}" data-date="{date(2025, 1, 1) + timedelta(days=i)}" data-level="{1 if i == 0 else 0}"></td>' for i in range(350))
    tips = '<tool-tip for="d0">2 contributions on January 1st.</tool-tip>' + "".join(
        f'<tool-tip for="d{i}">No contributions on January {i + 1}th.</tool-tip>' for i in range(1, 350)
    )
    parsed = fetch.parse_contributions(cells + tips)
    assert parsed[0]["count"] == 2
    assert parsed[1]["count"] == 0


def test_tooltip_counts_are_exact_and_never_derived_from_level():
    assert fetch.parse_contribution_count("No contributions on January 1st.") == 0
    assert fetch.parse_contribution_count("1 contribution on January 2nd.") == 1
    assert fetch.parse_contribution_count("6 contributions on January 3rd.") == 6
    html = "".join(
        f'<td class="ContributionCalendar-day" id="d{i}" data-date="{date(2025, 1, 1) + timedelta(days=i)}" data-level="4"></td>'
        for i in range(350)
    ) + '<tool-tip for="d0">6 contributions on January 1st.</tool-tip>' + "".join(
        f'<tool-tip for="d{i}">No contributions on January {i}th.</tool-tip>' for i in range(1, 350)
    )
    parsed = fetch.parse_contributions(html)
    assert parsed[0]["level"] == 4
    assert parsed[0]["count"] == 6
    assert sum(int(day["count"]) for day in parsed) == 6


def test_heatmap_svg_uses_levels_and_accessible_summary():
    payload = {"days": days([0, 1, 2, 3, 4]), "stats": fetch.calculate_stats(days([0, 1, 2, 3, 4]))}
    svg = render.svg_for(payload, "dark")
    assert 'viewBox="0 0 860 210"' in svg
    assert "GitHub contribution activity" in svg
    assert render.THEMES["dark"]["empty"] in svg
    assert render.THEMES["dark"]["levels"][3] in svg


def test_github_sunday_first_grid_mapping_for_known_active_days():
    start = render.calendar_start(["2025-10-05", "2026-10-07"])
    assert start == date(2025, 10, 5)
    assert render.grid_position(date(2026, 10, 6), start) == (52, 2)  # Tuesday
    assert render.grid_position(date(2026, 10, 7), start) == (52, 3)  # Wednesday


def test_calendar_start_does_not_shift_when_latest_day_is_midweek():
    start = render.calendar_start(["2025-10-05", "2026-10-07"])
    assert render.grid_position(date(2025, 10, 5), start) == (0, 0)
