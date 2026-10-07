#!/usr/bin/env python3
"""Generate an animated terminal boot card for the GitHub profile README."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    "dark": {"bg": "#0d1117", "primary": "#c9d1d9", "muted": "#8b949e", "accent": "#39c5cf"},
    "light": {"bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de", "primary": "#24292f", "muted": "#57606a", "accent": "#087f9d"},
}
LINES = [
    ("title", "mateus.profile", 0.20),
    ("muted", "> initializing profile...", 0.50),
    ("muted", "> loading modules...", 0.85),
    ("module", "LMS / Moodle", 1.20),
    ("module", "Python Automation", 1.50),
    ("module", "Backend / APIs", 1.80),
    ("module", "Applied AI", 2.10),
    ("module", "Real-world Projects", 2.40),
    ("ready", "> status: READY", 3.20),
    ("footer", "mode      production", 3.52),
    ("footer", "uptime    building since 2023", 3.70),
]


def animation(delay: float, static: bool) -> str:
    if static:
        return ""
    return (f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur=".20s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="-6 0" to="0 0" begin="{delay:.2f}s" dur=".20s" fill="freeze"/>')


def render(theme: str, static: bool) -> str:
    colors = THEMES[theme]
    panel = colors.get("panel", colors["bg"])
    border = colors.get("border", colors["muted"])
    rendered = []
    y = 70
    for kind, label, delay in LINES:
        if kind == "title":
            rendered.append(f'<g opacity="{"1" if static else "0"}">{animation(delay, static)}<text x="28" y="{y}" class="title">{label}</text></g>')
            y += 31
        elif kind == "muted":
            rendered.append(f'<g opacity="{"1" if static else "0"}">{animation(delay, static)}<text x="28" y="{y}" class="muted">{label}</text></g>')
            y += 28
        elif kind == "module":
            rendered.append(f'<g opacity="{"1" if static else "0"}">{animation(delay, static)}<text x="28" y="{y}" class="ok">[ OK ]</text><text x="85" y="{y}" class="primary">{label}</text></g>')
            y += 29
        elif kind == "ready":
            y = 343
            rendered.append(f'<g opacity="{"1" if static else "0"}">{animation(delay, static)}<text x="28" y="{y}" class="ready">{label}</text></g>')
            y += 42
        else:
            rendered.append(f'<g opacity="{"1" if static else "0"}">{animation(delay, static)}<text x="28" y="{y}" class="footer">{label}</text></g>')
            y += 22
    progress = []
    for index in range(12):
        begin = 2.58 + index * 0.045
        opacity = "1" if static else "0"
        animate = "" if static else f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.2f}s" dur=".12s" fill="freeze"/>'
        progress.append(f'<rect x="{29 + index * 14}" y="300" width="10" height="5" rx="1" fill="{colors["accent"]}" opacity="{opacity}">{animate}</rect>')
    progress_label = f'<g opacity="{"1" if static else "0"}">{animation(3.10, static)}<text x="28" y="324" class="muted">loading [████████████] 100%</text></g>'
    cursor = '' if static else '<text x="177" y="350" class="accent" opacity="0">_<animate attributeName="opacity" values="1;0;1;0;1;0;1" begin="3.32s" dur=".60s" repeatCount="1" fill="freeze"/></text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="350" height="430" viewBox="0 0 350 430" role="img" aria-labelledby="title desc">
<title id="title">Mateus Menezes profile boot sequence</title>
<desc id="desc">An animated terminal boot sequence listing Moodle, Python automation, backend APIs, applied AI, and real-world projects.</desc>
<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px}}.title{{fill:{colors["primary"]};font-size:18px;font-weight:700}}.primary{{fill:{colors["primary"]}}}.muted{{fill:{colors["muted"]}}}.ok{{fill:{colors["accent"]};font-weight:700}}.ready{{fill:{colors["accent"]};font-weight:700}}.footer{{fill:{colors["muted"]};font-size:11px}}.accent{{fill:{colors["accent"]};font-size:16px}}</style>
<rect width="350" height="430" rx="12" fill="{colors["bg"]}" stroke="{border}" stroke-opacity=".82"/>
<path d="M1 45H349V429H1Z" fill="{panel}" fill-opacity=".72"/>
<circle cx="28" cy="29" r="4" fill="{colors["accent"]}"/><text x="40" y="33" class="muted" style="font-size:10px">PROFILE BOOT / v1.0</text><path d="M28 44H322" stroke="{colors["muted"]}" stroke-opacity=".30"/>
{''.join(rendered)}{''.join(progress)}{progress_label}<path d="M28 365H322" stroke="{colors["muted"]}" stroke-opacity=".28"/>{cursor}</svg>'''


def main() -> None:
    destination = ROOT / "assets"
    if os.environ.get("BOOT_OUTPUT_DIR"):
        destination = Path(os.environ["BOOT_OUTPUT_DIR"])
    destination.mkdir(parents=True, exist_ok=True)
    static = os.environ.get("STATIC") == "1"
    for theme in THEMES:
        (destination / f"boot-card-{theme}.svg").write_text(render(theme, static), encoding="utf-8")
    print(f"Generated boot cards in {destination}")


if __name__ == "__main__":
    main()
