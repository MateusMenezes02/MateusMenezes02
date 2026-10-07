# Source portrait

Place a square or portrait-oriented photo at `source/profile.jpg`. For best results, use a well-lit image with a simple background. The pipeline uses `rembg` and OpenCV CLAHE when they are installed, but falls back safely to Pillow.

```sh
pip install -r scripts/requirements-photo.txt
python scripts/prep_photo.py source/profile.jpg source/prepared.png
python scripts/make_ascii_svg.py source/prepared.png
```

`prep_photo.py` performs background neutralization, grayscale conversion, local contrast enhancement, and final contrast correction. If you create a transparent cutout separately, supply it to the same command instead of the original photo.
