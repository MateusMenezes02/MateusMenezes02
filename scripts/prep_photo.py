#!/usr/bin/env python3
"""Prepare a portrait for high-contrast, background-neutral ASCII rendering.

Pillow is the only required image dependency. rembg and OpenCV are detected at
runtime and improve background removal and local contrast when installed.
"""
from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


def remove_background(image: Image.Image) -> Image.Image:
    """Return a cutout when rembg is available; otherwise preserve the source."""
    if image.mode == "RGBA" and image.getchannel("A").getextrema()[0] < 255:
        return image
    try:
        from rembg import remove  # type: ignore[import-not-found]
    except ImportError:
        print("Info: rembg is not installed; using the original background.", file=sys.stderr)
        return image
    try:
        result = remove(image)
        if isinstance(result, Image.Image):
            return result.convert("RGBA")
        return Image.open(BytesIO(result)).convert("RGBA")
    except Exception as exc:
        print(f"Warning: background removal was unavailable ({exc}); using the original image.", file=sys.stderr)
        return image


def local_contrast(image: Image.Image) -> Image.Image:
    """Apply CLAHE when OpenCV exists, with a robust Pillow-only fallback."""
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]
        values = np.array(image)
        return Image.fromarray(cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(values))
    except ImportError:
        return ImageOps.autocontrast(image, cutoff=1)
    except Exception as exc:
        print(f"Warning: CLAHE failed ({exc}); using automatic contrast.", file=sys.stderr)
        return ImageOps.autocontrast(image, cutoff=1)


def prepare(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Portrait not found: {source}")
    with Image.open(source) as opened:
        cutout = remove_background(opened.convert("RGBA"))
    white = Image.new("RGBA", cutout.size, "white")
    flattened = Image.alpha_composite(white, cutout).convert("L")
    prepared = local_contrast(flattened)
    prepared = ImageEnhance.Contrast(prepared).enhance(1.25)
    destination.parent.mkdir(parents=True, exist_ok=True)
    prepared.save(destination)
    print(f"Prepared ASCII source: {destination}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a portrait for ASCII conversion.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        prepare(args.source, args.destination)
    except (FileNotFoundError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
