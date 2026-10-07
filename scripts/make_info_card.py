#!/usr/bin/env python3
"""Generate the two theme-aware neofetch-style profile cards."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES = {"dark": ("#0d1117", "#e6edf3", "#8b949e", "#00bcd4"), "light": ("#ffffff", "#24292f", "#57606a", "#087f9d")}
LINES = [("Role", "LMS / Moodle Analyst"), ("Focus", "Automation · Backend · Applied AI"), ("Degree", "Computer Science"), ("", ""), ("Languages", "Python · JavaScript · SQL"), ("Backend", "FastAPI · REST APIs"), ("Frontend", "React · Next.js"), ("Data", "PostgreSQL · SQLite"), ("DevOps", "Docker · Git · GitHub"), ("Testing", "Pytest"), ("Automation", "Playwright"), ("LMS", "Moodle"), ("AI", "LLMs · ML · Generative AI"), ("", ""), ("Building", "SaaS · Automation · AI Tools")]


def make_svg(theme: str, static: bool) -> str:
    bg, text, muted, accent = THEMES[theme]
    rendered = []
    y = 63
    for index, (key, value) in enumerate(LINES):
        if not key:
            y += 8
            continue
        animation = "" if static else f'<animateTransform attributeName="transform" type="translate" from="8 0" to="0 0" begin="{index*.07:.2f}s" dur=".22s" fill="freeze"/><animate attributeName="opacity" from="0" to="1" begin="{index*.07:.2f}s" dur=".22s" fill="freeze"/>'
        opacity = "1" if static else "0"
        rendered.append(f'<g opacity="{opacity}">{animation}<text x="22" y="{y}" class="k">{key}</text><text x="119" y="{y}" class="v">{value}</text></g>')
        y += 24
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="510" height="430" viewBox="0 0 510 430" role="img" aria-labelledby="title"><title id="title">Mateus Menezes technical profile</title><style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}.k{{fill:{muted};font-size:12px}}.v{{fill:{text};font-size:12px}}.n{{fill:{text};font-size:18px;font-weight:700}}</style><rect width="510" height="430" rx="12" fill="{bg}" stroke="{muted}" stroke-opacity=".35"/><circle cx="25" cy="25" r="5" fill="{accent}"/><text x="40" y="31" class="n">Mateus Menezes</text><path d="M22 43H488" stroke="{muted}" stroke-opacity=".45"/>{''.join(rendered)}</svg>'''


def main() -> None:
    assets = ROOT / "assets"; assets.mkdir(exist_ok=True)
    static = os.environ.get("STATIC") == "1"
    for theme in THEMES:
        (assets / f"info-{theme}.svg").write_text(make_svg(theme, static), encoding="utf-8")


if __name__ == "__main__":
    main()
