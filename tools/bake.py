"""Bake the axolotl reference drawing into the particle file used by the site.

    python -P tools/bake.py tools/axolotl-reference.jpg assets/axolotl.v1.bin [--points N] [--debug]

Binary format "AXL2" (little endian), N points:
    offset 0        magic b"AXL2"
    offset 4        uint32 N
    offset 8        int16  pos[3N]   x, y, z in scene units * 1000 (body ~9.5 units tall, head towards +y)
    offset 8 + 6N   uint8  col[3N]   rgb
    offset 8 + 9N   uint8  geo[N]    distance along the body: 0 snout tip, 255 tail tip
    offset 8 + 10N  uint8  kind[N]   0 body, 1 gill, 2 eye, 3 limb
    offset 8 + 11N  uint8  part[N]   0 none; legs: 1 front left (x<0), 2 front right, 3 back left, 4 back right
    offset 8 + 12N  uint8  grow[N]   legs only: 0 at the shoulder/hip, 255 at the finger tips; 0 elsewhere
"""
import argparse
import struct

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.color import rgb2hsv
from skimage.graph import MCP_Geometric
from skimage.morphology import skeletonize

MAGIC = b"AXL2"
S = 1024            # working resolution
BODY_HEIGHT = 9.5   # scene units
GRADIENT = np.array([[0xf2, 0x7f, 0xa0], [0xd8, 0x47, 0x9a], [0x8d, 0x55, 0xd8], [0x4f, 0x8f, 0xe0]], np.float32) / 255
GILL_COLOR = np.array([0.93, 0.22, 0.55], np.float32)
EYE_COLOR = np.array([0.18, 0.09, 0.30], np.float32)


def _disk(r):
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xx ** 2 + yy ** 2 <= r ** 2


def _analyse(src):
    """Masks and per-pixel fields of the drawing."""
    img = np.asarray(Image.open(src).convert("RGB").resize((S, S), Image.LANCZOS)).astype(np.float32) / 255
    lum = img @ np.array([0.299, 0.587, 0.114], np.float32)
    sat = rgb2hsv(img)[..., 1]

    # Silhouette: anything noticeably away from white
    mask = ((1 - img.min(axis=2)) > 0.045) | (sat > 0.06)
    mask = ndi.binary_opening(mask, iterations=1)
    lab, n = ndi.label(mask)
    sizes = ndi.sum(mask, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes > 40
    mask = ndi.binary_fill_holes(keep[lab])

    dist = ndi.distance_transform_edt(mask)

    # Distance along the body from the snout, measured inside the silhouette
    ys, xs = np.nonzero(mask)
    top = ys.min()
    snout = (int(top + 3), int(np.round(xs[ys < top + 6].mean())))
    geod, _ = MCP_Geometric(np.where(mask, 1.0, np.inf)).find_costs([snout])
    geod[~np.isfinite(geod)] = 0
    geo = np.clip(geod / np.percentile(geod[mask], 99.8), 0, 1)

    red, green, blue = img[..., 0], img[..., 1], img[..., 2]
    gill = mask & (sat > 0.42) & (red - green > 0.35) & (blue > green)
    gill = ndi.binary_dilation(gill, iterations=1) & mask
    gill_zone = ndi.binary_closing(gill, iterations=8) & mask
    eye = mask & (lum < 0.35) & (geo < 0.1) & ~ndi.binary_dilation(gill_zone, iterations=6)

    # Trunk, head and thick tail survive a wide opening; legs (palms included) do not
    trunk = ndi.binary_opening(mask, structure=_disk(34))
    limb = mask & ~trunk & ~gill_zone & ~eye & (geo > 0.12) & (geo < 0.66)
    limb = ndi.binary_opening(limb, iterations=1)

    return dict(img=img, lum=lum, mask=mask, dist=dist, geo=geo, gill=gill, gill_zone=gill_zone,
                eye=eye, trunk=trunk, limb=limb, center_x=(xs.min() + xs.max()) / 2,
                center_y=(ys.min() + ys.max()) / 2, span=ys.max() - ys.min())


def _legs(a):
    """Label the four legs (1 FL, 2 FR, 3 BL, 4 BR) and how far each pixel is from the body."""
    lab, n = ndi.label(ndi.binary_dilation(a["limb"], iterations=3) & a["mask"] & ~a["trunk"] & ~a["gill_zone"])
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    biggest = np.argsort(sizes)[::-1][:4] + 1
    part = np.zeros(lab.shape, np.uint8)
    reach = ndi.distance_transform_edt(~a["trunk"])
    grow = np.zeros(lab.shape, np.float32)
    for c in biggest:
        comp = lab == c
        ys, xs = np.nonzero(comp)
        left = xs.mean() < a["center_x"]
        front = a["geo"][comp].mean() < 0.4
        part[comp] = (1 if left else 2) if front else (3 if left else 4)
        r = reach[comp]
        grow[comp] = np.clip(r / max(np.percentile(r, 99), 1), 0, 1)
    return part, grow


def bake(src, n=34000, seed=11):
    rng = np.random.default_rng(seed)
    a = _analyse(src)
    mask, img, lum, geo = a["mask"], a["img"], a["lum"], a["geo"]
    part_px, grow_px = _legs(a)

    # More particles on edges, texture and fine parts so the detail reads
    gy, gx = np.gradient(ndi.gaussian_filter(lum, 0.8))
    edge = np.hypot(gx, gy)
    edge /= np.percentile(edge[mask], 98) + 1e-6
    w = 0.35 + 1.4 * np.clip(edge, 0, 1.5) + 0.5 * a["gill"] + 1.5 * a["eye"] + 0.6 * (part_px > 0)
    w = np.where(mask, w, 0).ravel()
    idx = rng.choice(w.size, size=n, replace=False, p=w / w.sum())
    py, px = np.divmod(idx, S)
    fy = py + rng.random(n) - 0.5
    fx = px + rng.random(n) - 0.5

    # Half of the gill particles sit exactly on the filament skeleton so strands read as lines
    skel_y, skel_x = np.nonzero(skeletonize(a["gill"]))
    on_gill = np.nonzero(a["gill"][py, px])[0]
    pick = rng.choice(on_gill, size=len(on_gill) // 2, replace=False)
    s = rng.integers(0, len(skel_y), len(pick))
    py[pick], px[pick] = skel_y[s], skel_x[s]
    fy[pick] = skel_y[s] + (rng.random(len(pick)) - 0.5) * 0.6
    fx[pick] = skel_x[s] + (rng.random(len(pick)) - 0.5) * 0.6

    kind = np.zeros(n, np.uint8)
    part = part_px[py, px]
    kind[(a["limb"][py, px]) | (part > 0)] = 3
    kind[a["gill_zone"][py, px]] = 1
    kind[a["eye"][py, px]] = 2
    part[kind != 3] = 0
    grow = np.where(part > 0, grow_px[py, px] * 255, 0).round().astype(np.uint8)

    # Depth: rounded body, thin gills and fingers
    t = a["dist"][py, px]
    side = np.where(rng.random(n) < 0.82, 1.0, -1.0)
    z = side * t * 0.8 * (0.8 + 0.2 * rng.random(n))
    inner = rng.random(n) < 0.12
    z[inner] *= rng.random(inner.sum())
    z[kind == 1] = rng.normal(0, 1.2, (kind == 1).sum()) + 14
    z[kind == 2] = t[kind == 2] * 0.8 + 6

    u = BODY_HEIGHT / a["span"]
    pos = np.stack([(fx - a["center_x"]) * u, -(fy - a["center_y"]) * u, z * u], 1).astype(np.float32)

    # Colour: brand gradient along the body, shaded by the drawing so its texture survives
    g = geo[py, px] * (len(GRADIENT) - 1)
    i0 = np.clip(np.floor(g).astype(int), 0, len(GRADIENT) - 2)
    f = (g - i0)[:, None]
    col = GRADIENT[i0] * (1 - f) + GRADIENT[i0 + 1] * f
    shade = np.clip((lum[py, px] - 0.55) / 0.45, 0, 1)[:, None]
    col = col * (0.78 + 0.22 * shade)
    hi = np.clip((lum[py, px] - 0.9) / 0.1, 0, 1)[:, None]
    col = col * (1 - 0.35 * hi) + 0.35 * hi
    col = col * 0.9 + img[py, px] * 0.1
    vivid = a["gill"][py, px]
    col[vivid] = GILL_COLOR * 0.7 + img[py, px][vivid] * 0.3
    col[kind == 2] = EYE_COLOR

    return dict(
        pos=pos,
        col=(np.clip(col, 0, 1) * 255).round().astype(np.uint8),
        geo=(geo[py, px] * 255).round().astype(np.uint8),
        kind=kind,
        part=part.astype(np.uint8),
        grow=grow,
        _debug=a,
        _part_px=part_px,
    )


def write_bin(path, data):
    n = len(data["kind"])
    with open(path, "wb") as fh:
        fh.write(MAGIC)
        fh.write(struct.pack("<I", n))
        fh.write((data["pos"] * 1000).round().astype("<i2").tobytes())
        for key in ("col", "geo", "kind", "part", "grow"):
            fh.write(np.ascontiguousarray(data[key], np.uint8).tobytes())


def read_bin(path):
    raw = open(path, "rb").read()
    if raw[:4] != MAGIC:
        raise ValueError("not an AXL2 file")
    n = struct.unpack_from("<I", raw, 4)[0]
    pos = np.frombuffer(raw, "<i2", 3 * n, 8).reshape(n, 3).astype(np.float32) / 1000
    o = 8 + 6 * n
    col = np.frombuffer(raw, np.uint8, 3 * n, o).reshape(n, 3)
    o += 3 * n
    out = dict(pos=pos, col=col)
    for key in ("geo", "kind", "part", "grow"):
        out[key] = np.frombuffer(raw, np.uint8, n, o)
        o += n
    return out


def _write_debug(path, data):
    a, part_px = data["_debug"], data["_part_px"]
    dbg = np.ones((S, S, 3), np.float32)
    dbg[a["mask"]] = 0.85
    leg_cols = {1: [0.2, 0.5, 1], 2: [0.2, 0.8, 0.5], 3: [1, 0.6, 0.1], 4: [0.6, 0.3, 0.9]}
    for p, c in leg_cols.items():
        dbg[part_px == p] = c
    dbg[a["gill_zone"]] = [1, 0.6, 0.8]
    dbg[a["gill"]] = [1, 0.2, 0.6]
    dbg[a["eye"]] = [0, 0, 0]
    Image.fromarray((dbg * 255).astype(np.uint8)).save(path + ".parts.png")
    Image.fromarray((np.where(a["mask"], a["geo"], 1) * 255).astype(np.uint8)).save(path + ".geo.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--points", type=int, default=34000)
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    data = bake(args.src, args.points)
    write_bin(args.out, data)
    if args.debug:
        _write_debug(args.out, data)
    k = data["kind"]
    print(f"{len(k)} points: gill {(k == 1).sum()}, eye {(k == 2).sum()}, limb {(k == 3).sum()}, "
          f"legs {[int((data['part'] == p).sum()) for p in (1, 2, 3, 4)]}")


if __name__ == "__main__":
    main()
