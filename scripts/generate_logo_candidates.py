#!/usr/bin/env python3
"""Generate logo candidates for the Luminous Morna VS Code theme.

Everything is drawn from scratch with PIL (no AI images) at 3x supersampling,
then downsampled to 512 and 128 px. Also builds contact sheets + a
small-size readability strip.

Run from the project root:  python3 scripts/generate_logo_candidates.py
(Relative paths only - the project path contains non-ASCII characters.)
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = "store-assets/logo-candidates"
BASE = 512
SS = 3
S = BASE * SS

# --------------------------------------------------------------------------
# palette (values taken from themes/*.json)
# --------------------------------------------------------------------------

DARK = dict(
    bg="#2A2919",
    surface="#353425",
    fg="#F1F0E9",
    muted="#9D9C92",
    accent="#25A096",
    accent2="#3C9C9F",
    purple="#88748C",
    green="#889B52",
    gold="#D4A72C",
    red="#C64952",
    cream="#FCFBED",
    beam="#FCFBED",
)

LIGHT = dict(
    bg="#FCFBED",
    surface="#EFEEE1",
    fg="#2D2C25",
    muted="#848379",
    accent="#1D7D75",
    accent2="#3C9C9F",
    purple="#88748C",
    green="#889B52",
    gold="#A9862F",
    red="#C64952",
    cream="#FFFFFF",
    beam="#2D2C25",
)

ACCENT_ORDER = ("accent", "purple", "green", "gold")


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# --------------------------------------------------------------------------
# drawing helpers
# --------------------------------------------------------------------------

def radial_glow(size, center, radius, color, alpha=140, power=2.0, steps=44):
    """Soft radial halo, returned as an RGBA layer to alpha_composite."""
    grad = Image.new("L", (size, size), 0)
    gd = ImageDraw.Draw(grad)
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(alpha * ((1.0 - i / steps) ** power))
        if a <= 0:
            continue
        gd.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], fill=a)
    solid = Image.new("RGBA", (size, size), color + (255,))
    solid.putalpha(grad)
    return solid


def plate(size, bg, radius_ratio=0.22):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1],
                        radius=size * radius_ratio, fill=hx(bg) + (255,))
    return img


def round_line(d, p1, p2, width, color, caps=True):
    d.line([p1, p2], fill=color, width=int(round(width)))
    if caps:
        r = width / 2.0
        for p in (p1, p2):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def polyline(d, pts, width, color, caps=True):
    d.line(pts, fill=color, width=int(round(width)), joint="curve")
    if caps:
        r = width / 2.0
        for p in (pts[0], pts[-1]):
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def wave_points(size, y, amp, x0, x1, cycles=1.0, phase=0.0, n=72):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        pts.append((x, y - amp * math.sin(2 * math.pi * cycles * t + phase)))
    return pts


def star_points(cx, cy, r_out, r_in):
    pts = []
    for k in range(8):
        ang = math.radians(k * 45 - 90)
        r = r_out if k % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


# --------------------------------------------------------------------------
# concepts
# --------------------------------------------------------------------------

def c_aperture_dawn(size, P):
    """Sun rising behind a horizon line - 'luminous' glow."""
    img = plate(size, P["bg"])
    cx, cy, R = 0.5 * size, 0.600 * size, 0.220 * size
    img.alpha_composite(radial_glow(size, (cx, cy), 0.47 * size, hx(P["accent"]), alpha=125))
    d = ImageDraw.Draw(img)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=hx(P["accent"]) + (62,))
    round_line(d, (0.130 * size, cy), (0.870 * size, cy), 0.030 * size, hx(P["fg"]))
    d.pieslice([cx - R, cy - R, cx + R, cy + R], 180, 360, fill=hx(P["accent"]))
    for ang in (58, 90, 122):
        a = math.radians(ang)
        p1 = (cx + 0.300 * size * math.cos(a), cy - 0.300 * size * math.sin(a))
        p2 = (cx + 0.365 * size * math.cos(a), cy - 0.365 * size * math.sin(a))
        round_line(d, p1, p2, 0.020 * size, hx(P["fg"]))
    return img


def c_prism_spectra(size, P):
    """A beam entering a prism and splitting into the theme accent colours."""
    img = plate(size, P["bg"])
    img.alpha_composite(radial_glow(size, (0.52 * size, 0.50 * size), 0.40 * size,
                                    hx(P["accent"]), alpha=70))
    d = ImageDraw.Draw(img)
    apex = (0.500 * size, 0.250 * size)
    bl = (0.290 * size, 0.710 * size)
    br = (0.710 * size, 0.710 * size)
    # outgoing beams (behind the prism)
    src = (0.585 * size, 0.470 * size)
    for i, key in enumerate(ACCENT_ORDER):
        dst = (0.930 * size, (0.315 + 0.115 * i) * size)
        round_line(d, src, dst, 0.022 * size, hx(P[key]))
    # incoming beam
    round_line(d, (0.080 * size, 0.470 * size), (0.400 * size, 0.470 * size),
               0.026 * size, hx(P["beam"]))
    # prism
    d.polygon([apex, bl, br], fill=hx(P["surface"]))
    d.line([apex, bl, br, apex], fill=hx(P["accent"]), width=int(round(0.030 * size)),
           joint="curve")
    return img


def c_bracket_orbit(size, P):
    """Angle brackets wrapping a glowing core - code + light."""
    img = plate(size, P["bg"])
    cx, cy = 0.5 * size, 0.5 * size
    img.alpha_composite(radial_glow(size, (cx, cy), 0.34 * size, hx(P["accent"]), alpha=165))
    d = ImageDraw.Draw(img)
    w = 0.046 * size
    for mirror in (1, -1):
        pts = [(cx + mirror * 0.148 * size, 0.320 * size),
               (cx + mirror * 0.244 * size, 0.500 * size),
               (cx + mirror * 0.148 * size, 0.680 * size)]
        polyline(d, pts, w, hx(P["accent"]))
    R = 0.092 * size
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=hx(P["accent"]))
    d.ellipse([cx - R * 0.62, cy - R * 0.62, cx + R * 0.62, cy + R * 0.62],
              fill=hx(P["cream"]))
    return img


def c_morna_breeze(size, P):
    """Three flowing waves - 'morna', the warm breeze."""
    img = plate(size, P["bg"])
    img.alpha_composite(radial_glow(size, (0.5 * size, 0.5 * size), 0.44 * size,
                                    hx(P["accent"]), alpha=95))
    d = ImageDraw.Draw(img)
    bands = ((0.360, 0.062, 0.046, "accent"),
             (0.500, 0.052, 0.038, "accent2"),
             (0.640, 0.040, 0.030, "gold"))
    for y0, amp, w, key in bands:
        pts = wave_points(size, y0 * size, amp * size, 0.140 * size, 0.860 * size, 1.0, 0.25 * math.pi)
        polyline(d, pts, w * size, hx(P[key]))
    return img


def c_palette_grid(size, P):
    """2x2 tiles of the syntax palette with a light sparkle."""
    img = plate(size, P["bg"])
    img.alpha_composite(radial_glow(size, (0.5 * size, 0.5 * size), 0.46 * size,
                                    hx(P["accent"]), alpha=85))
    d = ImageDraw.Draw(img)
    t = 0.268 * size
    gap = 0.050 * size
    total = 2 * t + gap
    x0 = (size - total) / 2.0
    y0 = (size - total) / 2.0
    rr = 0.050 * size
    for i, key in enumerate(ACCENT_ORDER):
        cx = x0 + (i % 2) * (t + gap)
        cy = y0 + (i // 2) * (t + gap)
        d.rounded_rectangle([cx, cy, cx + t, cy + t], radius=rr, fill=hx(P[key]))
    # a sparkle glinting in the corner of the first tile - always on a
    # saturated fill, so it reads on both the dark and the light plate
    sx = x0 + t * 0.775
    sy = y0 + t * 0.225
    img.alpha_composite(radial_glow(size, (sx, sy), 0.15 * size, hx(P["cream"]), alpha=110))
    d = ImageDraw.Draw(img)
    d.polygon(star_points(sx, sy, 0.056 * size, 0.016 * size), fill=hx(P["cream"]))
    return img


def c_arched_sunrise(size, P):
    """Concentric arches over a baseline - a rising sun."""
    img = plate(size, P["bg"])
    cx, by = 0.5 * size, 0.690 * size
    img.alpha_composite(radial_glow(size, (cx, by - 0.15 * size), 0.42 * size,
                                    hx(P["accent"]), alpha=95))
    d = ImageDraw.Draw(img)
    for R, w, key in ((0.110, 0.030, "gold"),
                      (0.190, 0.030, "accent2"),
                      (0.270, 0.028, "accent")):
        d.arc([cx - R * size, by - R * size, cx + R * size, by + R * size],
              180, 360, fill=hx(P[key]), width=int(round(w * size)))
    round_line(d, (0.135 * size, by), (0.865 * size, by), 0.032 * size, hx(P["fg"]))
    return img


def c_eclipse_duo(size, P):
    """One disc, two halves: the light and the dark theme."""
    img = plate(size, P["bg"])
    cx, cy = 0.5 * size, 0.5 * size
    R = 0.245 * size
    img.alpha_composite(radial_glow(size, (cx - 0.09 * size, cy), 0.44 * size,
                                    hx(P["accent"]), alpha=90))
    d = ImageDraw.Draw(img)
    ring = 0.028 * size
    inner = R - 0.058 * size
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=hx("#FCFBED"))
    d.pieslice([cx - inner, cy - inner, cx + inner, cy + inner], -90, 90,
               fill=hx("#2A2919"))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=hx(P["accent"]),
              width=int(round(ring)))
    round_line(d, (cx, cy - inner - 0.010 * size), (cx, cy + inner + 0.010 * size),
               0.014 * size, hx(P["accent"]))
    return img


CONCEPTS = [
    ("aperture-dawn", "1. Aperture Dawn", c_aperture_dawn),
    ("prism-spectra", "2. Prism Spectra", c_prism_spectra),
    ("bracket-orbit", "3. Bracket Orbit", c_bracket_orbit),
    ("morna-breeze", "4. Morna Breeze", c_morna_breeze),
    ("palette-grid", "5. Palette Grid", c_palette_grid),
    ("arched-sunrise", "6. Arched Sunrise", c_arched_sunrise),
    ("eclipse-duo", "7. Eclipse Duo", c_eclipse_duo),
]

# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

FONT_CANDIDATES = (
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


def load_font(px):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, px)
            except OSError:
                continue
    return ImageFont.load_default()


def text_size(draw, txt, font):
    box = draw.textbbox((0, 0), txt, font=font)
    return box[2] - box[0], box[3] - box[1]


def draw_lines(draw, cx, top, lines, font, fill, line_h):
    y = top
    for line in lines:
        tw, _ = text_size(draw, line, font)
        draw.text((cx - tw / 2, y), line, font=font, fill=fill)
        y += line_h


def sheet(items, out_path, bg, fg, tile, cols, gap, margin, title, label_px):
    """items: list of (label, PIL image already at `tile` px)."""
    rows = math.ceil(len(items) / cols)
    label_lines = max(len(label.split("\n")) for label, _ in items)
    label_h = int(label_px * 2.1) + (label_lines - 1) * int(label_px * 1.25)
    title_h = int(label_px * 2.6)
    w = margin * 2 + cols * tile + (cols - 1) * gap
    h = margin + title_h + int(margin * 0.5) + rows * (tile + label_h) \
        + (rows - 1) * gap + margin

    grid_left = margin
    grid_right = margin + cols * tile + (cols - 1) * gap
    assert grid_right == w - margin, "right baseline mismatch"
    grid_bottom = margin + title_h + int(margin * 0.5) + rows * (tile + label_h) \
        + (rows - 1) * gap
    assert grid_bottom <= h - margin, "bottom overflow"

    img = Image.new("RGBA", (w, h), hx(bg) + (255,))
    d = ImageDraw.Draw(img)
    font_title = load_font(int(label_px * 1.5))
    font_label = load_font(label_px)

    d.text((margin, margin), title, font=font_title, fill=hx(fg) + (255,))

    top = margin + title_h + int(margin * 0.5)
    prev_bottom = 0
    for idx, (label, im) in enumerate(items):
        cx = grid_left + (idx % cols) * (tile + gap)
        cy = top + (idx // cols) * (tile + label_h + gap)
        if idx % cols == 0 and idx:
            assert cy > prev_bottom, "rows overlap"
        prev_bottom = cy + tile + label_h
        assert cx + tile <= grid_right, "tile right overflow"
        assert cy + tile + label_h <= grid_bottom, "tile bottom overflow"
        img.alpha_composite(im.convert("RGBA"), (int(cx), int(cy)))
        draw_lines(d, cx + tile / 2.0, cy + tile + int(label_px * 0.45),
                   label.split("\n"), font_label, hx(fg) + (235,),
                   int(label_px * 1.25))
    img.convert("RGB").save(out_path, quality=95)
    return out_path


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []

    for slug, label, fn in CONCEPTS:
        cdir = os.path.join(OUT, "concepts", slug)
        os.makedirs(cdir, exist_ok=True)
        renditions = {}
        for variant, pal in (("dark", DARK), ("light", LIGHT)):
            big = fn(S, pal)
            im512 = big.resize((BASE, BASE), Image.LANCZOS)
            im128 = im512.resize((128, 128), Image.LANCZOS)
            im512.save(os.path.join(cdir, "%s-512.png" % variant))
            im128.save(os.path.join(cdir, "%s-128.png" % variant))
            renditions[variant] = im512
            made.append(os.path.join(cdir, "%s-512.png" % variant))
        # transparency check: the plate must stay opaque in the middle
        assert renditions["dark"].convert("RGBA").getpixel((BASE // 2, 6))[3] == 255
        print("  ok  %-16s %s" % (slug, label))

    tile = 256
    for variant, bg, fg in (("dark", "#141310", "#EDECE0"),
                            ("light", "#E3E2D5", "#2D2C25")):
        items = []
        for slug, label, _ in CONCEPTS:
            p = os.path.join(OUT, "concepts", slug, "%s-512.png" % variant)
            items.append((label, Image.open(p).convert("RGBA")
                          .resize((tile, tile), Image.LANCZOS)))
        out = os.path.join(OUT, "contact-sheet-%s.png" % variant)
        sheet(items, out, bg, fg, tile, 4, 30, 45,
              "Luminous Morna Theme - logo concepts (%s plate)" % variant, 26)
        print("sheet", out)

    # small-size readability strip
    items = []
    for slug, label, _ in CONCEPTS:
        p = os.path.join(OUT, "concepts", slug, "dark-512.png")
        short = label.split(". ", 1)[1].replace(" ", "\n")
        items.append((short, Image.open(p).convert("RGBA").resize((112, 112), Image.LANCZOS)))
    sheet(items, os.path.join(OUT, "readability-128.png"), "#141310", "#EDECE0",
          112, 7, 30, 45, "Small size check - 112 px", 19)

    print("\n%d files + 3 sheets under %s/" % (len(made), OUT))


if __name__ == "__main__":
    main()
