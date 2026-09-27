#!/usr/bin/env python3
"""Render the final extension icon (concept 1 - Aperture Dawn).

Reuses the concept renderer from generate_logo_candidates.py so the icon and
the candidate sheet can never drift apart.

Run from the project root:  python3 scripts/generate_icon.py
"""

import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_logo_candidates as logo  # noqa: E402

OUT = "store-assets"


def main():
    os.makedirs(OUT, exist_ok=True)
    master = logo.c_aperture_dawn(logo.S, logo.LIGHT).resize(
        (logo.BASE, logo.BASE), Image.LANCZOS)

    for size in (512, 256, 128):
        im = master.resize((size, size), Image.LANCZOS)
        path = os.path.join(OUT, "icon.png" if size == 128 else "icon-%d.png" % size)
        im.save(path)
        print("icon", path, "%dx%d" % (size, size))

    assert os.path.exists(os.path.join(OUT, "icon.png"))


if __name__ == "__main__":
    main()
