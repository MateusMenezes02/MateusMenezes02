#!/usr/bin/env python3
"""Convert a prepared portrait into compact, line-animated ASCII SVGs."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RAMP = " .`:-=+*cs#%@"
GRID = (72, 46)
THEMES = {"dark": ("#0d1117", "#72d8e8"), "light": ("#ffffff", "#087f9d")}


def ascii_lines(image: Image.Image, width: int = GRID[0], height: int = GRID[1]) -> list[str]:
    """Preserve the portrait composition while compensating for narrow glyphs."""
    grayscale = ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(1.12)
    target_ratio = (width * 0.60) / height
    source_ratio = grayscale.width / grayscale.height
    if source_ratio > target_ratio:
        crop_width = int(grayscale.height * target_ratio)
        left = (grayscale.width - crop_width) // 2
        grayscale = grayscale.crop((left, 0, left + crop_width, grayscale.height))
    else:
        crop_height = int(grayscale.width / target_ratio)
        top = max(0, (grayscale.height - crop_height) // 6)
        grayscale = grayscale.crop((0, top, grayscale.width, min(grayscale.height, top + crop_height)))
    fitted = grayscale.resize((width, height), Image.Resampling.LANCZOS)
    return ["".join(RAMP[fitted.getpixel((x, y)) * (len(RAMP) - 1) // 255] for x in range(width)) for y in range(height)]


def render(lines: list[str], theme: str, static: bool) -> str:
    bg, ink = THEMES[theme]
    rows = []
    for index, line in enumerate(lines):
        opacity = "1" if static else "0"
        animation = "" if static else f'<animate attributeName="opacity" from="0" to="1" begin="{index * .028:.3f}s" dur=".10s" fill="freeze"/>'
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows.append(f'<text x="14" y="{25 + index * 8.1:.1f}" opacity="{opacity}">{safe}{animation}</text>')
    cursor = "" if static else '<rect x="330" y="395" width="4" height="8"><animate attributeName="opacity" values="1;0;1" dur=".5s" begin="1.4s" repeatCount="2" fill="freeze"/></rect>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="350" height="430" viewBox="0 0 350 430" role="img" aria-labelledby="title desc"><title id="title">ASCII portrait of Mateus Menezes</title><desc id="desc">A monochrome ASCII portrait generated from Mateus Menezes&apos;s profile photograph.</desc><rect width="350" height="430" rx="12" fill="{bg}"/><g fill="{ink}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="7.5">{"".join(rows)}{cursor}</g></svg>'


def main() -> int:
    parser = argparse.ArgumentParser(description="Render theme-aware ASCII portrait SVGs.")
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Portrait not found: {args.image}")
    with Image.open(args.image) as portrait:
        lines = ascii_lines(portrait)
    static = os.environ.get("STATIC") == "1"
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for theme in THEMES:
        (assets / f"ascii-{theme}.svg").write_text(render(lines, theme, static), encoding="utf-8")
    print("Generated assets/ascii-dark.svg and assets/ascii-light.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
