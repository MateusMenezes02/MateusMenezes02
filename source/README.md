# Source portrait

Place a square or portrait-oriented photo at `source/profile.jpg`. For best results, use a well-lit image with a simple or transparent background.

```sh
pip install -r scripts/requirements-photo.txt
python scripts/prep_photo.py source/profile.jpg source/prepared.png
python scripts/make_ascii_svg.py source/prepared.png
```

`prep_photo.py` performs a predictable local preparation pass. If you use a separate background-removal tool, supply its transparent output to this script.
