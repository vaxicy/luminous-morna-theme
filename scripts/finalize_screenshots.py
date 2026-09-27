#!/usr/bin/env python3
"""Move the raw VS Code captures into store-assets/screenshots/en/.

capture-screenshots.ps1 writes raw windows to an ASCII temp folder (GDI+ and
non-ASCII paths do not always get along); this script resizes them down to a
sane width and saves the final marketplace / README screenshots.

Run from the project root:  python3 scripts/finalize_screenshots.py
"""

import os
import sys

from PIL import Image, ImageStat

OUT_DIR = "store-assets/screenshots/en"
MAX_WIDTH = 1920

# titleBar.activeBackground of each variant, used to confirm the Windows frame
# was trimmed (a dark 1px OS border would drag these means far below the value)
EXPECTED_TOP_ROW = {"dark": (0x3D, 0x3C, 0x2E), "light": (0xE5, 0xE4, 0xD8)}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = os.path.join(os.environ.get("TEMP", ""), "morna-shot-%s")

    for variant in ("dark", "light"):
        src = os.path.join(tmp % variant, "raw-%s.png" % variant)
        if not os.path.exists(src):
            print("missing raw capture for '%s' - run capture-screenshots.ps1 first" % variant)
            sys.exit(1)

        im = Image.open(src).convert("RGB")
        row = ImageStat.Stat(im.crop((0, 0, im.width, 1))).mean
        col = ImageStat.Stat(im.crop((0, 0, 1, im.height))).mean
        want = EXPECTED_TOP_ROW[variant]
        print("first row mean %s / first col mean %s / expected title bar %s"
              % (tuple(round(c) for c in row), tuple(round(c) for c in col), want))

        if im.width > MAX_WIDTH:
            height = round(im.height * MAX_WIDTH / im.width)
            im = im.resize((MAX_WIDTH, height), Image.LANCZOS)
        dst = os.path.join(OUT_DIR, "luminous-morna-theme-%s.png" % variant)
        im.save(dst, optimize=True)
        print("%-42s %dx%d  %.2f MB" % (dst, im.width, im.height,
                                        os.path.getsize(dst) / 1024 / 1024))


if __name__ == "__main__":
    main()
