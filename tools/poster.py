"""Render the still fallback image of the particle axolotl.

    python -P tools/poster.py assets/axolotl.v1.bin assets/axolotl-poster.v1.webp
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bake import read_bin  # noqa: E402


def render_poster(data, out, size=(720, 880), tilt=-0.38, rot_z=0.36, scale=1.0):
    """Same pose as the live scene (tilt around x, then rotate around z), orthographic, transparent background."""
    p = data["pos"].astype(np.float64)
    c, s = np.cos(tilt), np.sin(tilt)
    y, z = p[:, 1] * c - p[:, 2] * s, p[:, 1] * s + p[:, 2] * c
    c, s = np.cos(rot_z), np.sin(rot_z)
    x, y = p[:, 0] * c - y * s, p[:, 0] * s + y * c

    ss = 2                                     # supersample for soft round dots
    W, H = size[0] * ss, size[1] * ss
    span = max((x.max() - x.min()) / W, (y.max() - y.min()) / H) / (0.92 * scale)
    px = ((x - (x.max() + x.min()) / 2) / span + W / 2).astype(int)
    py = ((-(y - (y.max() + y.min()) / 2)) / span + H / 2).astype(int)
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)

    order = np.argsort(z[ok])                  # back to front
    px, py = px[ok][order], py[ok][order]
    col = data["col"][ok][order].astype(np.float64) / 255

    weight = np.zeros((H, W))
    rgb = np.zeros((H, W, 3))
    np.add.at(weight, (py, px), 0.85)
    for ch in range(3):
        np.add.at(rgb[..., ch], (py, px), 0.85 * col[:, ch])
    weight = ndi.gaussian_filter(weight, 1.6 * ss / 2)
    for ch in range(3):
        rgb[..., ch] = ndi.gaussian_filter(rgb[..., ch], 1.6 * ss / 2)

    alpha = 1 - np.exp(-weight * 10)
    colour = rgb / np.maximum(weight, 1e-6)[..., None]
    rgba = np.dstack([np.clip(colour, 0, 1), alpha])
    im = Image.fromarray((rgba * 255).round().astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
    im.save(out, "WEBP", quality=72, alpha_quality=55, method=6)


if __name__ == "__main__":
    render_poster(read_bin(sys.argv[1]), sys.argv[2])
