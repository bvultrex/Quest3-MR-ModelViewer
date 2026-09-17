#!/usr/bin/env python3
from pathlib import Path
import math
import struct
import sys
import zlib

# Dependency-free 512x512 PNG generator for the Quest launcher icon.
# Draw at 2x and box-filter down for clean edges without Pillow/ImageMagick.
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('questmr_icon.png')
S = 2
W = H = 512 * S
pixels = bytearray(W * H * 4)


def put(x, y, rgba):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 4
        pixels[i:i+4] = bytes(rgba)


def fill_rounded_rect(x0, y0, x1, y1, radius, rgba):
    x0 *= S; y0 *= S; x1 *= S; y1 *= S; radius *= S
    r2 = radius * radius
    for y in range(y0, y1):
        for x in range(x0, x1):
            cx = x
            cy = y
            if x < x0 + radius:
                cx = x0 + radius
            elif x >= x1 - radius:
                cx = x1 - radius - 1
            if y < y0 + radius:
                cy = y0 + radius
            elif y >= y1 - radius:
                cy = y1 - radius - 1
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                put(x, y, rgba)


def fill_polygon(points, rgba):
    pts = [(int(x * S), int(y * S)) for x, y in points]
    min_y = max(0, min(y for _, y in pts))
    max_y = min(H - 1, max(y for _, y in pts))
    n = len(pts)
    for y in range(min_y, max_y + 1):
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if y1 == y2:
                continue
            if y >= min(y1, y2) and y < max(y1, y2):
                t = (y - y1) / (y2 - y1)
                xs.append(int(round(x1 + t * (x2 - x1))))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, xs[i])
            xb = min(W - 1, xs[i + 1])
            for x in range(xa, xb + 1):
                put(x, y, rgba)


def draw_disc(cx, cy, r, rgba):
    cx *= S; cy *= S; r *= S
    rr = r * r
    for y in range(max(0, cy-r), min(H, cy+r+1)):
        dy2 = (y-cy)*(y-cy)
        dx = int(math.sqrt(max(0, rr-dy2)))
        for x in range(max(0, cx-dx), min(W, cx+dx+1)):
            put(x, y, rgba)


def draw_line(x0, y0, x1, y1, width, rgba):
    x0 *= S; y0 *= S; x1 *= S; y1 *= S; width *= S
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    rad = max(1, width // 2)
    for s in range(steps + 1):
        t = s / steps
        x = int(round(x0 + dx * t))
        y = int(round(y0 + dy * t))
        rr = rad * rad
        for yy in range(y-rad, y+rad+1):
            if yy < 0 or yy >= H:
                continue
            ddy = yy-y
            span = int(math.sqrt(max(0, rr-ddy*ddy)))
            for xx in range(x-span, x+span+1):
                if 0 <= xx < W:
                    put(xx, yy, rgba)


# Transparent corners with a substantial safe-zone tile. No neon/glow.
fill_rounded_rect(28, 28, 484, 484, 92, (24, 30, 39, 255))

# A depth plane that disappears behind the model: tiny visual shorthand for MR occlusion.
draw_line(76, 286, 205, 286, 9, (112, 139, 172, 255))
draw_line(307, 286, 436, 286, 9, (112, 139, 172, 255))
draw_disc(76, 286, 4, (190, 204, 220, 255))
draw_disc(436, 286, 4, (190, 204, 220, 255))

# Isometric model cube.
top = [(256, 112), (386, 181), (256, 250), (126, 181)]
left = [(126, 181), (256, 250), (256, 406), (126, 337)]
right = [(256, 250), (386, 181), (386, 337), (256, 406)]
fill_polygon(top, (232, 238, 246, 255))
fill_polygon(left, (73, 142, 214, 255))
fill_polygon(right, (43, 91, 158, 255))

# Crisp structural edges.
edge = (245, 248, 252, 255)
for a, b in [
    ((256,112),(386,181)), ((386,181),(256,250)), ((256,250),(126,181)), ((126,181),(256,112)),
    ((126,181),(126,337)), ((126,337),(256,406)), ((256,406),(386,337)), ((386,337),(386,181)),
    ((256,250),(256,406)),
]:
    draw_line(*a, *b, 5, edge)

# Small center marker, suggestive of placement/inspection without text.
draw_disc(256, 250, 9, (24, 30, 39, 255))
draw_disc(256, 250, 4, (245, 248, 252, 255))

# 2x -> 1x box downsample.
out_w = out_h = 512
raw = bytearray(out_w * out_h * 4)
for y in range(out_h):
    for x in range(out_w):
        sums = [0, 0, 0, 0]
        for oy in (0, 1):
            for ox in (0, 1):
                i = (((y * 2 + oy) * W) + (x * 2 + ox)) * 4
                for c in range(4):
                    sums[c] += pixels[i+c]
        j = (y * out_w + x) * 4
        raw[j:j+4] = bytes(v // 4 for v in sums)

# PNG with RGBA8, no external dependencies.
scan = bytearray()
stride = out_w * 4
for y in range(out_h):
    scan.append(0)
    scan.extend(raw[y*stride:(y+1)*stride])


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

png = bytearray(b'\x89PNG\r\n\x1a\n')
png += chunk(b'IHDR', struct.pack('>IIBBBBB', out_w, out_h, 8, 6, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(bytes(scan), 9))
png += chunk(b'IEND', b'')

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(png)
print(f'Generated Quest launcher icon: {OUT} ({len(png)} bytes, 512x512 RGBA)')
