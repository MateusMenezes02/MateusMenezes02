#!/usr/bin/env python3
"""Render a sparse, face-focused ASCII portrait from a transparent cutout."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RAMP = "  .:*#@"
THEMES = {"dark": ("#0d1117", "#c9d1d9"), "light": ("#ffffff", "#24292f")}


def portrait_crop(image: Image.Image) -> Image.Image:
    """Frame head and upper shoulders from the supplied transparent portrait."""
    rgba = image.convert("RGBA")
    bounds = rgba.getchannel("A").getbbox() or (0, 0, rgba.width, rgba.height)
    left, top, right, bottom = bounds
    width, height = right - left, bottom - top
    return rgba.crop((left + int(width * 0.12), top, right - int(width * 0.12), top + int(height * 0.66)))


def ascii_lines(image: Image.Image, columns: int) -> list[str]:
    """Combine foreground, posterized dark regions, and edges into sparse glyphs."""
    crop = portrait_crop(image)
    rows = max(32, min(42, round(columns * (crop.height / crop.width) * 0.60)))
    alpha = crop.getchannel("A").resize((columns, rows), Image.Resampling.LANCZOS)
    gray = ImageEnhance.Contrast(ImageOps.grayscale(crop)).enhance(1.35)
    posterized = ImageOps.posterize(gray, 3).resize((columns, rows), Image.Resampling.LANCZOS)
    edges = ImageEnhance.Contrast(gray).enhance(1.7).filter(ImageFilter.FIND_EDGES).resize((columns, rows), Image.Resampling.LANCZOS)
    lines: list[str] = []
    for y in range(rows):
        row = []
        for x in range(columns):
            mask = alpha.getpixel((x, y))
            if mask < 70:
                row.append(" ")
                continue
            darkness = 255 - posterized.getpixel((x, y))
            edge = edges.getpixel((x, y))
            importance = max(darkness, int(edge * 0.70) if darkness > 18 else 0) * mask // 255
            if importance < 44:
                row.append(" ")
            elif importance < 70:
                row.append(".")
            elif importance < 112:
                row.append(":")
            elif importance < 158:
                row.append("*")
            elif importance < 205:
                row.append("#")
            else:
                row.append("@")
        lines.append("".join(row).rstrip())
    return lines


def render(lines: list[str], theme: str, static: bool) -> str:
    bg, ink = THEMES[theme]
    columns = max(len(line) for line in lines) if lines else 1
    font_size = min(8.0, 304 / (columns * 0.60))
    line_height = font_size * 1.08
    x = (350 - columns * font_size * 0.60) / 2
    drawing_height = len(lines) * line_height
    start_y = (430 - drawing_height) / 2 + font_size
    rows = []
    for index, line in enumerate(lines):
        opacity = "1" if static else "0"
        animation = "" if static else f'<animate attributeName="opacity" from="0" to="1" begin="{index * .022:.3f}s" dur=".12s" fill="freeze"/>'
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows.append(f'<text x="{x:.1f}" y="{start_y + index * line_height:.1f}" opacity="{opacity}">{safe}{animation}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="350" height="430" viewBox="0 0 350 430" role="img" aria-labelledby="title desc"><title id="title">Minimal ASCII portrait of Mateus Menezes</title><desc id="desc">A sparse monochrome ASCII portrait emphasizing Mateus Menezes&apos;s face and upper shoulders.</desc><rect width="350" height="430" rx="12" fill="{bg}"/><g fill="{ink}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{font_size:.2f}">{"".join(rows)}</g></svg>'


def write_pair(lines: list[str], destination: Path, static: bool) -> None:
    if destination.suffix == ".svg":
        destination.write_text(render(lines, "dark", static), encoding="utf-8")
        return
    destination.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (destination / f"ascii-{theme}.svg").write_text(render(lines, theme, static), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render minimal theme-aware ASCII portrait SVGs.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--columns", type=int, default=52, choices=range(40, 81))
    parser.add_argument("--preview", type=Path, help="Write one dark-theme comparison SVG instead of final assets.")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Portrait not found: {args.image}")
    with Image.open(args.image) as portrait:
        lines = ascii_lines(portrait, args.columns)
    static = os.environ.get("STATIC") == "1"
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        write_pair(lines, args.preview, static)
        print(f"Generated {args.preview}")
    else:
        write_pair(lines, ROOT / "assets", static)
        print("Generated assets/ascii-dark.svg and assets/ascii-light.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
