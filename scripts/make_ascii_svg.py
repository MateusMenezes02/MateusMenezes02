#!/usr/bin/env python3
"""Render a minimal, face-first ASCII avatar from the real portrait cutout."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RAMP = "  .:-*#@"
THEMES = {
    "dark": {"panel": "#0d1117", "portrait": "#c9d1d9", "texture": "#8b949e"},
    "light": {"panel": "#ffffff", "portrait": "#24292f", "texture": "#57606a"},
}


def face_crop(image: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int] | None]:
    """Detect a face with OpenCV and expand it to an avatar bust crop.

    The fallback coordinates are tuned to the supplied profile cutout and avoid
    using the full-person alpha bounding box.
    """
    rgba = image.convert("RGBA")
    face: tuple[int, int, int, int] | None = None
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]

        array = np.array(rgba.convert("RGB"))
        gray = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        if len(faces):
            face = tuple(map(int, max(faces, key=lambda item: item[2] * item[3])))
    except (ImportError, OSError):
        pass
    if face:
        x, y, width, height = face
        left = x - int(width * 0.45)
        top = y - int(height * 0.35)
        right = x + width + int(width * 0.45)
        bottom = y + height + int(height * 0.70)
    else:
        left, top = int(rgba.width * 0.25), int(rgba.height * 0.10)
        right, bottom = int(rgba.width * 0.78), int(rgba.height * 0.63)
    left, top = max(0, left), max(0, top)
    right, bottom = min(rgba.width, right), min(rgba.height, bottom)
    return rgba.crop((left, top, right, bottom)), face


def ascii_lines(image: Image.Image, columns: int) -> tuple[list[str], tuple[int, int, int, int] | None]:
    """Use foreground, CLAHE, blur, posterization and edges without filling skin."""
    crop, face = face_crop(image)
    rows = round(columns * (crop.height / crop.width) * 0.75)
    rows = max(34, min(44, rows))
    alpha = crop.getchannel("A").resize((columns, rows), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(crop)
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]

        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(np.array(gray))
        gray = Image.fromarray(enhanced)
    except ImportError:
        gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.20).filter(ImageFilter.GaussianBlur(radius=0.45))
    posterized = ImageOps.posterize(gray, 3).resize((columns, rows), Image.Resampling.LANCZOS)
    edge_source = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edge_source).enhance(1.35).resize((columns, rows), Image.Resampling.LANCZOS)
    lines: list[str] = []
    for y in range(rows):
        row = []
        for x in range(columns):
            mask = alpha.getpixel((x, y))
            if mask < 85:
                row.append(" ")
                continue
            darkness = 255 - posterized.getpixel((x, y))
            edge = edges.getpixel((x, y))
            # White clothing is removed: it contributes only if it has a strong edge.
            edge_importance = int(edge * 0.58) if darkness > 30 else 0
            importance = max(darkness, edge_importance) * mask // 255
            if importance < 48:
                row.append(" ")
            elif importance < 74:
                row.append(".")
            elif importance < 108:
                row.append(":")
            elif importance < 150:
                row.append("-")
            elif importance < 190:
                row.append("*")
            elif importance < 224:
                row.append("#")
            else:
                row.append("@")
        lines.append("".join(row).rstrip())
    return lines, face


def decorative_background(theme: str) -> str:
    """Create a sparse, deterministic terminal texture outside the face halo."""
    chars = (".", ":", "`", "-", "'")
    marks = []
    for y in range(30, 405, 14):
        for x in range(22, 330, 15):
            # Elliptical exclusion zone keeps the portrait immediately dominant.
            halo = ((x - 175) / 137) ** 2 + ((y - 215) / 179) ** 2
            token = (x * 17 + y * 31 + x * y) % 23
            if halo > 1.0 and token in (0, 1, 2):
                marks.append(f'<text x="{x}" y="{y}">{chars[token % len(chars)]}</text>')
    return f'<g fill="{THEMES[theme]["texture"]}" opacity=".16" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="7">{"".join(marks)}</g>'


def render(lines: list[str], theme: str, static: bool) -> str:
    colors = THEMES[theme]
    columns = max(len(line) for line in lines) if lines else 1
    font_size = min(9.0, 296 / (columns * 0.60))
    line_height = font_size * 1.08
    x = (350 - columns * font_size * 0.60) / 2
    start_y = (430 - len(lines) * line_height) / 2 + font_size
    rows = []
    for index, line in enumerate(lines):
        opacity = "1" if static else "0"
        animation = "" if static else f'<animate attributeName="opacity" from="0" to="1" begin="{index * .018:.3f}s" dur=".11s" fill="freeze"/>'
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        rows.append(f'<text x="{x:.1f}" y="{start_y + index * line_height:.1f}" opacity="{opacity}">{safe}{animation}</text>')
    portrait = f'<g transform="translate(175 215) scale(1.065) translate(-175 -215)" fill="{colors["portrait"]}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{font_size:.2f}">{"".join(rows)}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="350" height="430" viewBox="0 0 350 430" role="img" aria-labelledby="title desc"><title id="title">ASCII avatar of Mateus Menezes</title><desc id="desc">A minimal monochrome ASCII bust portrait emphasizing Mateus Menezes&apos;s face, with a subtle peripheral terminal texture.</desc><rect width="350" height="430" rx="12" fill="{colors["panel"]}"/>{decorative_background(theme)}{portrait}</svg>'


def main() -> int:
    parser = argparse.ArgumentParser(description="Render face-focused ASCII portrait SVGs.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--columns", type=int, default=46, choices=range(40, 61))
    parser.add_argument("--preview", type=Path, help="Write one dark-theme local preview SVG instead of assets.")
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Portrait not found: {args.image}")
    with Image.open(args.image) as portrait:
        lines, face = ascii_lines(portrait, args.columns)
    destination = args.preview or ROOT / "assets"
    static = os.environ.get("STATIC") == "1"
    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(render(lines, "dark", static), encoding="utf-8")
        print(f"Generated {args.preview}")
    else:
        for theme in THEMES:
            (destination / f"ascii-v2-{theme}.svg").write_text(render(lines, theme, static), encoding="utf-8")
        print("Generated assets/ascii-v2-dark.svg and assets/ascii-v2-light.svg")
    print(f"Face detection: {face or 'fallback crop'}; grid: {args.columns}x{len(lines)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
