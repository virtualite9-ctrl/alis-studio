#!/usr/bin/env python3
"""Build Alis Studio's app icon (.icns) — no SVG tooling needed.

If packaging/icon_source.png exists (the artwork Alis Studio generated for itself), it is
framed into a macOS squircle; otherwise a procedural clay-squircle + sparkle mark is drawn.
Either way, writes a full macOS .iconset and runs `iconutil` to assemble a multi-resolution
AppIcon.icns. Pillow is the only dependency.

    python3 packaging/make_icon.py [OUT.icns]      # default: packaging/AppIcon.icns
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageOps

CLAY = (196, 98, 63)        # --clay  #c4623f  (light theme brand color)
CLAY_TOP = (214, 121, 90)   # lighter clay for the top of the gradient (depth)
WHITE = (255, 255, 255)

# (iconset filename, pixel size) — the set Apple's iconutil expects
ICONSET = [
    ("icon_16x16.png", 16), ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32), ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128), ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256), ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512), ("icon_512x512@2x.png", 1024),
]


def _sparkle(cx, cy, outer, inner, points=4, rot=-math.pi / 2):
    """Vertices of a concave n-point star (a 'sparkle') centered at (cx, cy)."""
    out = []
    for i in range(points * 2):
        r = outer if i % 2 == 0 else inner
        a = rot + i * math.pi / points
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def _vertical_gradient(size, top, bottom):
    """An (size x size) RGBA vertical gradient, built cheaply from a 1-px column."""
    col = Image.new("RGBA", (1, size))
    px = col.load()
    for y in range(size):
        t = y / (size - 1)
        px[0, y] = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
    return col.resize((size, size))


def _squircle_points(S, margin, n=5.0, steps=720):
    """Outline of a macOS-style squircle (superellipse |x|^n + |y|^n = 1) in an S×S canvas."""
    c = (S - 1) / 2.0
    half = (S - 2 * margin) / 2.0
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        ct, st = math.cos(t), math.sin(t)
        pts.append((c + half * math.copysign(abs(ct) ** (2.0 / n), ct),
                    c + half * math.copysign(abs(st) ** (2.0 / n), st)))
    return pts


# Generated source art (made by Alis Studio itself). If present, it's framed into the squircle
# instead of the procedural mark below.
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon_source.png")


def _frame_source(size) -> Image.Image:
    """Frame the source artwork (icon_source.png) into the macOS squircle tile."""
    ss = 4
    S = size * ss
    margin = round(S * 0.085)
    src = ImageOps.fit(Image.open(SOURCE).convert("RGBA"), (S, S), Image.LANCZOS)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(_squircle_points(S, margin), fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(src, (0, 0), mask)
    return img.resize((size, size), Image.LANCZOS)


def render_master(size=1024) -> Image.Image:
    """Render the icon at high resolution. Prefer the generated source art (icon_source.png,
    made by Alis Studio itself); otherwise fall back to the procedural clay-sparkle mark."""
    if os.path.exists(SOURCE):
        return _frame_source(size)
    ss = 4  # supersample for smooth squircle + sparkle edges
    S = size * ss
    margin = round(S * 0.085)             # macOS icon-grid margin
    art = S - 2 * margin
    cx = cy = S / 2.0

    # Compose gradient → soft glow → sparkles, then clip to the squircle in one paste so the
    # glow stays inside the icon shape.
    inside = _vertical_gradient(S, CLAY_TOP, CLAY)

    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gr = art * 0.30
    ImageDraw.Draw(glow).ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=(255, 255, 255, 60))
    inside.alpha_composite(glow.filter(ImageFilter.GaussianBlur(gr * 0.55)))  # soft light behind the mark

    d = ImageDraw.Draw(inside)
    d.polygon(_sparkle(cx, cy, outer=art * 0.345, inner=art * 0.345 * 0.34), fill=WHITE)
    # small accent sparkle, lower-right — echoes the two-star UI logo
    sx, sy = cx + art * 0.205, cy + art * 0.215
    d.polygon(_sparkle(sx, sy, outer=art * 0.105, inner=art * 0.105 * 0.36), fill=WHITE)

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(_squircle_points(S, margin), fill=255)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    img.paste(inside, (0, 0), mask)
    return img.resize((size, size), Image.LANCZOS)


def main(argv):
    out = os.path.abspath(argv[1]) if len(argv) > 1 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "AppIcon.icns")
    master = render_master(1024)
    with tempfile.TemporaryDirectory() as tmp:
        iconset = os.path.join(tmp, "AppIcon.iconset")
        os.makedirs(iconset)
        for name, sz in ICONSET:
            master.resize((sz, sz), Image.LANCZOS).save(os.path.join(iconset, name))
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv)
