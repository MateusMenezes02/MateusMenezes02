#!/usr/bin/env python3
"""Prepare a portrait for ASCII conversion; background removal is optional/local."""
from __future__ import annotations
import argparse
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps


def prepare(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGBA")
    # Preserve an already-transparent cutout, compositing it on white for predictable ASCII.
    background = Image.new("RGBA", image.size, "white")
    image = Image.alpha_composite(background, image).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flatten, grayscale, and improve contrast for an ASCII portrait.")
    parser.add_argument("source", type=Path); parser.add_argument("destination", type=Path)
    args = parser.parse_args(); prepare(args.source, args.destination)
