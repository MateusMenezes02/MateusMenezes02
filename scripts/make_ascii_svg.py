#!/usr/bin/env python3
"""Convert a prepared portrait to a compact, line-animated ASCII SVG."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RAMP = " .`:-=+*cs#%@"
THEMES = {"dark": ("#0d1117", "#72d8e8"), "light": ("#ffffff", "#087f9d")}


def ascii_lines(image: Image.Image, width: int = 80, height: int = 45) -> list[str]:
    fitted = ImageOps.fit(image.convert("L"), (width, height))
    return ["".join(RAMP[p * (len(RAMP) - 1) // 255] for p in [fitted.getpixel((x, y)) for x in range(width)]) for y in range(height)]


def render(lines: list[str], theme: str, static: bool) -> str:
    bg, ink = THEMES[theme]; rows = []
    for i, line in enumerate(lines):
        opacity = "1" if static else "0"
        anim = "" if static else f'<animate attributeName="opacity" from="0" to="1" begin="{i*.035:.3f}s" dur=".08s" fill="freeze"/>'
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows.append(f'<text x="12" y="{22+i*9}" opacity="{opacity}">{safe}{anim}</text>')
    cursor = "" if static else '<rect x="338" y="416" width="5" height="9"><animate attributeName="opacity" values="1;0;1" dur=".55s" begin="1.6s" repeatCount="2" fill="freeze"/></rect>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="350" height="430" viewBox="0 0 350 430" role="img" aria-labelledby="title"><title id="title">ASCII portrait</title><rect width="350" height="430" rx="12" fill="{bg}"/><g fill="{ink}" font-family="ui-monospace,monospace" font-size="9">{"".join(rows)}{cursor}</g></svg>'


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("image", type=Path); args = parser.parse_args()
    lines = ascii_lines(Image.open(args.image)); static = os.environ.get("STATIC") == "1"
    assets = ROOT / "assets"; assets.mkdir(exist_ok=True)
    for theme in THEMES: (assets / f"ascii-{theme}.svg").write_text(render(lines, theme, static), encoding="utf-8")


if __name__ == "__main__": main()
