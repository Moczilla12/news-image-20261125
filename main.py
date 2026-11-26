#!/usr/bin/env python3
"""news-image-20261125 v2 — 'The World in One Day'

One-image broadsheet summary of Wednesday 25 November 2026 world news.
44 stories: 3 heroes + 12 illustrated cards + 29 numbered briefs.
All art is drawn/vector (no photos). Deterministic: two runs are byte-identical.
Writes entry.png to $MAKEFUN_OUTPUT_DIR when set, else next to this file.
Python 3.13, stdlib + PIL only, no local imports, no network.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (17, 17, 17)
MUTED = (96, 96, 90)
RED = (176, 30, 36)
NAVY = (27, 42, 74)
SLATE = (46, 74, 107)
GOLD = (200, 162, 74)
LINE = (180, 172, 156)
CARD_BG = (255, 255, 255)
SEA = (227, 235, 239)
LAND = (220, 213, 194)
LAND_LINE = (178, 168, 148)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def F_SERIF(s):
    return font("DejaVuSerif-Bold.ttf", s)


def F_SANS(s):
    return font("DejaVuSans.ttf", s)


def F_SANSB(s):
    return font("DejaVuSans-Bold.ttf", s)


# ---------------------------------------------------------------- text utils
def wrap(d, text, fnt, max_w):
    """Greedy word wrap; returns list of lines."""
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(d, text, fnt, max_w, max_lines):
    """Wrap and truncate to max_lines, appending an ellipsis if cut."""
    lines = wrap(d, text, fnt, max_w)
    if len(lines) <= max_lines:
        return lines
    out = lines[:max_lines]
    while out and d.textlength(out[-1] + " …", font=fnt) > max_w:
        out[-1] = out[-1][:-1]
    out[-1] = (out[-1] + " …").strip()
    return out


def para(d, x, y, lines, fnt, fill, leading):
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def badge(d, x, y, label):
    """Small badge pill; returns width used."""
    fnt = F_SANSB(8)
    w = int(d.textlength(label, font=fnt)) + 10
    h = 12
    color = RED if label == "CLAIM" else (NAVY if label == "OFFICIAL" else (90, 90, 86))
    d.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=color)
    d.text((x + 5, y + 2), label, font=fnt, fill=(255, 255, 255))
    return w


# ---------------------------------------------------------------- scene art
def _sky(d, box, top, bot):
    """Vertical gradient sky inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    steps = max(1, y1 - y0)
    for i in range(steps):
        t = i / steps
        c = tuple(int(top[j] + (bot[j] - top[j]) * t) for j in range(3))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def scene(d, kind, box):
    """Draw a small vector scene inside box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx, cy = x0 + w // 2, y0 + h // 2

    if kind == "tariff":
        _sky(d, box, (214, 226, 232), (240, 236, 224))
        # sea
        d.rectangle([x0, y1 - 18, x1, y1], fill=(70, 120, 160))
        # cargo ship hull
        d.polygon([(x0 + 10, y1 - 18), (x1 - 10, y1 - 18), (x1 - 22, y1 - 6),
                   (x0 + 22, y1 - 6)], fill=(52, 52, 58))
        # container stacks on deck (2 high)
        cols = [(196, 52, 48), (38, 90, 130), (176, 30, 36)]
        for i, c in enumerate(cols):
            bx = x0 + 18 + i * ((w - 36) // 3)
            bw2 = (w - 36) // 3 - 6
            d.rectangle([bx, y1 - 48, bx + bw2, y1 - 34], fill=c)
            d.rectangle([bx, y1 - 62, bx + bw2, y1 - 49], fill=c)
        # gantry crane silhouette on the left
        d.line([(x0 + 10, y0 + 10), (x0 + 10, y1 - 48)], fill=INK, width=3)
        d.line([(x0 + 10, y0 + 10), (x0 + w // 2, y0 + 10)], fill=INK, width=3)
        d.line([(x0 + w // 2, y0 + 10), (x0 + w // 2, y0 + 26)], fill=INK, width=2)
        # red tariff bar
        d.rectangle([x0, y1 - 14, x1, y1], fill=RED)
        d.text((x0 + 6, y1 - 13), "20%  ·  15%  ·  35%", font=F_SANSB(9), fill=(255, 255, 255))

    elif kind == "chip":
        d.rectangle(box, fill=(18, 28, 52))
        # falling chart
        pts = [(x0 + 6, y0 + 12), (x0 + int(w * 0.28), y0 + int(h * 0.28)),
               (x0 + int(w * 0.5), y0 + int(h * 0.22)), (x0 + int(w * 0.72), y0 + int(h * 0.62)),
               (x1 - 6, y1 - 10)]
        d.line(pts, fill=(255, 84, 84), width=3)
        for px, py in pts:
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255))
        # fab building
        d.rectangle([x0 + 8, y1 - 26, x0 + 52, y1 - 4], fill=(70, 90, 130))
        for i in range(4):
            d.rectangle([x0 + 13 + i * 10, y1 - 21, x0 + 19 + i * 10, y1 - 12],
                        fill=(255, 214, 90))
        d.text((x1 - 62, y1 - 16), "−6.2%", font=F_SANSB(13), fill=(255, 84, 84))

    elif kind == "rocket":
        _sky(d, box, (16, 24, 54), (58, 74, 122))
        for sx, sy in [(0.12, 0.2), (0.3, 0.12), (0.55, 0.3), (0.78, 0.14),
                       (0.88, 0.4), (0.45, 0.45), (0.2, 0.55)]:
            d.ellipse([x0 + w * sx - 1, y0 + h * sy - 1,
                       x0 + w * sx + 1, y0 + h * sy + 1], fill=(255, 255, 255))
        # station: hub + panels
        d.rectangle([x1 - 78, y0 + 12, x1 - 44, y0 + 22], fill=(150, 160, 180))
        d.rectangle([x1 - 96, y0 + 15, x1 - 78, y0 + 19], fill=(90, 120, 170))
        d.rectangle([x1 - 44, y0 + 15, x1 - 26, y0 + 19], fill=(90, 120, 170))
        d.ellipse([x1 - 64, y0 + 8, x1 - 58, y0 + 14], fill=(255, 255, 255))
        # rocket
        rx = x0 + int(w * 0.32)
        d.polygon([(rx, y0 + 22), (rx - 7, y0 + 42), (rx + 7, y0 + 42)], fill=RED)
        d.rectangle([rx - 7, y0 + 42, rx + 7, y0 + h - 18], fill=(245, 245, 245))
        d.rectangle([rx - 7, y0 + 56, rx + 7, y0 + 62], fill=NAVY)
        d.polygon([(rx - 7, y0 + h - 18), (rx + 7, y0 + h - 18),
                   (rx + 3, y0 + h - 6), (rx - 3, y0 + h - 6)], fill=(255, 170, 40))
        d.polygon([(rx - 12, y0 + h - 24), (rx - 7, y0 + h - 30),
                   (rx - 7, y0 + h - 16)], fill=RED)
        d.polygon([(rx + 12, y0 + h - 24), (rx + 7, y0 + h - 30),
                   (rx + 7, y0 + h - 16)], fill=RED)

    elif kind == "fire":
        _sky(d, box, (60, 52, 44), (150, 110, 70))
        # tanker silhouette
        d.rectangle([x0 + 8, y1 - 26, x1 - 8, y1 - 12], fill=(40, 36, 34))
        d.rectangle([x1 - 34, y1 - 40, x1 - 12, y1 - 26], fill=(40, 36, 34))
        # flames
        for fx, fh, fc in [(0.25, 0.62, (255, 120, 20)), (0.45, 0.85, (255, 190, 40)),
                           (0.62, 0.7, (255, 120, 20)), (0.78, 0.5, (255, 190, 40))]:
            bx = x0 + w * fx
            d.polygon([(bx - 12, y1 - 26), (bx, y1 - 26 - h * fh),
                       (bx + 12, y1 - 26)], fill=fc)
        # smoke
        for sx, sy, r in [(0.3, 0.18, 7), (0.5, 0.12, 9), (0.68, 0.2, 6)]:
            d.ellipse([x0 + w * sx - r, y0 + h * sy - r,
                       x0 + w * sx + r, y0 + h * sy + r], fill=(120, 115, 108))

    elif kind == "mine":
        d.rectangle(box, fill=(122, 94, 66))
        d.rectangle([x0, y0, x1, y0 + int(h * 0.3)], fill=(168, 140, 108))
        # shaft
        d.rectangle([cx - 16, y0 + int(h * 0.3), cx + 16, y1 - 8], fill=(52, 40, 30))
        d.rectangle([cx - 16, y0 + int(h * 0.3), cx + 16, y0 + int(h * 0.3) + 6],
                    fill=(30, 24, 20))
        # water at bottom
        d.rectangle([cx - 16, y1 - 18, cx + 16, y1 - 8], fill=(60, 120, 170))
        # headframe
        d.line([(cx - 26, y0 + 6), (cx - 16, y0 + int(h * 0.3))], fill=INK, width=2)
        d.line([(cx + 26, y0 + 6), (cx + 16, y0 + int(h * 0.3))], fill=INK, width=2)
        d.line([(cx - 26, y0 + 6), (cx + 26, y0 + 6)], fill=INK, width=2)
        d.ellipse([cx - 3, y0 + 2, cx + 3, y0 + 8], fill=(255, 214, 90))

    elif kind == "energy":
        _sky(d, box, (232, 228, 216), (246, 242, 232))
        # bill paper
        d.rectangle([x0 + 10, y0 + 8, x0 + int(w * 0.55), y1 - 8], fill=(255, 255, 255),
                    outline=(150, 140, 120))
        for i in range(4):
            d.line([(x0 + 16, y0 + 16 + i * 9), (x0 + int(w * 0.55) - 8, y0 + 16 + i * 9)],
                   fill=(170, 160, 140), width=1)
        # lightning bolt
        bx = x0 + int(w * 0.74)
        d.polygon([(bx + 6, y0 + 6), (bx - 8, y0 + int(h * 0.55)), (bx + 2, y0 + int(h * 0.55)),
                   (bx - 6, y1 - 6), (bx + 10, y0 + int(h * 0.45)), (bx, y0 + int(h * 0.45))],
                  fill=(255, 190, 40))
        d.text((x0 + int(w * 0.58), y1 - 16), "£2,166", font=F_SANSB(12), fill=RED)

    elif kind == "port":
        _sky(d, box, (206, 220, 228), (238, 234, 222))
        # sea
        d.rectangle([x0, y1 - 16, x1, y1], fill=(70, 120, 160))
        # cranes
        for kx in (0.18, 0.55):
            bx = x0 + w * kx
            d.line([(bx, y0 + 8), (bx, y1 - 16)], fill=INK, width=2)
            d.line([(bx, y0 + 8), (bx + 26, y0 + 14)], fill=INK, width=2)
            d.line([(bx + 26, y0 + 14), (bx + 26, y0 + 26)], fill=INK, width=1)
        # containers
        d.rectangle([x0 + 8, y1 - 30, x0 + 44, y1 - 18], fill=(196, 52, 48))
        d.rectangle([x0 + 48, y1 - 30, x0 + 84, y1 - 18], fill=(38, 90, 130))
        # ship
        d.polygon([(x1 - 90, y1 - 16), (x1 - 12, y1 - 16), (x1 - 22, y1 - 6),
                   (x1 - 80, y1 - 6)], fill=(60, 60, 66))
        d.rectangle([x1 - 66, y1 - 28, x1 - 34, y1 - 16], fill=(245, 245, 245))

    elif kind == "tankersea":
        _sky(d, box, (210, 224, 232), (240, 238, 230))
        d.rectangle([x0, y1 - 20, x1, y1], fill=(60, 105, 150))
        # tanker
        d.polygon([(x0 + 10, y1 - 20), (x1 - 10, y1 - 20), (x1 - 22, y1 - 8),
                   (x0 + 22, y1 - 8)], fill=(52, 52, 58))
        d.rectangle([x1 - 44, y1 - 36, x1 - 18, y1 - 20], fill=(52, 52, 58))
        # sea mine: spiky circle
        mx, my = x0 + int(w * 0.68), y0 + int(h * 0.42)
        for a in range(0, 360, 45):
            r = 11
            x2 = mx + r * math.cos(math.radians(a))
            y2 = my + r * math.sin(math.radians(a))
            d.line([(mx, my), (x2, y2)], fill=INK, width=2)
        d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=(30, 30, 30))
        # red CLAIM ring
        d.ellipse([mx - 14, my - 14, mx + 14, my + 14], outline=RED, width=2)

    elif kind == "drone":
        _sky(d, box, (30, 28, 40), (90, 70, 60))
        # refinery silhouette below
        for tx, tw, th in [(0.1, 0.16, 0.4), (0.32, 0.12, 0.55), (0.52, 0.18, 0.35)]:
            d.rectangle([x0 + w * tx, y1 - h * th, x0 + w * (tx + tw), y1 - 4],
                        fill=(50, 46, 42))
        # explosion burst
        ex, ey = x0 + int(w * 0.38), y0 + int(h * 0.42)
        for r, c in [(16, (255, 170, 40)), (10, (255, 120, 20)), (5, (255, 220, 120))]:
            d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=c)
        # drone quadcopter
        dx, dy = x0 + int(w * 0.78), y0 + int(h * 0.25)
        d.rectangle([dx - 8, dy - 3, dx + 8, dy + 3], fill=(230, 230, 230))
        for px in (-12, 12):
            d.ellipse([dx + px - 5, dy - 6, dx + px + 5, dy + 2],
                      outline=(230, 230, 230), width=1)
        d.line([(dx, dy + 3), (dx, dy + 10)], fill=(230, 230, 230), width=1)

    elif kind == "gaza":
        _sky(d, box, (240, 180, 110), (250, 220, 160))
        # building silhouettes
        for bx, bw, bh in [(0.05, 0.22, 0.55), (0.3, 0.18, 0.7), (0.52, 0.2, 0.5),
                           (0.75, 0.2, 0.62)]:
            d.rectangle([x0 + w * bx, y1 - h * bh, x0 + w * (bx + bw), y1],
                        fill=(90, 70, 58))
            for wy in range(2):
                d.rectangle([x0 + w * bx + 5, y1 - h * bh + 8 + wy * 12,
                             x0 + w * bx + 11, y1 - h * bh + 14 + wy * 12],
                            fill=(255, 214, 120))
        # broken tower
        d.polygon([(x0 + w * 0.3, y1 - h * 0.7), (x0 + w * 0.38, y1 - h * 0.86),
                   (x0 + w * 0.46, y1 - h * 0.7)], fill=(70, 54, 44))
        # sun
        d.ellipse([x1 - 34, y0 + 6, x1 - 12, y0 + 28], fill=(255, 120, 40))

    elif kind == "gdp":
        _sky(d, box, (238, 240, 234), (250, 248, 240))
        # bars rising
        vals = [0.3, 0.42, 0.38, 0.55, 0.8]
        bw = (w - 24) // 5
        for i, v in enumerate(vals):
            bx = x0 + 12 + i * bw
            bh = int((h - 22) * v)
            c = (46, 120, 70) if i == 4 else (110, 150, 120)
            d.rectangle([bx, y1 - 8 - bh, bx + bw - 6, y1 - 8], fill=c)
        d.text((x0 + 8, y0 + 4), "4.3%", font=F_SANSB(14), fill=(30, 100, 60))

    elif kind == "refinery":
        _sky(d, box, (70, 60, 52), (170, 130, 90))
        # towers
        for tx, tw, th in [(0.12, 0.14, 0.6), (0.32, 0.1, 0.75), (0.5, 0.16, 0.5)]:
            d.rectangle([x0 + w * tx, y1 - h * th, x0 + w * (tx + tw), y1 - 6],
                        fill=(80, 76, 70))
            d.line([(x0 + w * tx, y1 - h * th), (x0 + w * (tx + tw), y1 - h * th)],
                   fill=(200, 190, 170), width=1)
        # flare flame
        fx = x0 + w * 0.37
        d.polygon([(fx - 8, y1 - h * 0.75), (fx, y1 - h * 0.95), (fx + 8, y1 - h * 0.75)],
                  fill=(255, 170, 40))
        # drone quadcopter
        dx, dy = x0 + int(w * 0.78), y0 + int(h * 0.28)
        d.rectangle([dx - 8, dy - 3, dx + 8, dy + 3], fill=INK)
        for px in (-12, 12):
            d.ellipse([dx + px - 5, dy - 6, dx + px + 5, dy + 2], outline=INK, width=1)
        d.line([(dx, dy + 3), (dx, dy + 10)], fill=INK, width=1)

    elif kind == "garment":
        _sky(d, box, (226, 232, 236), (244, 240, 230))
        # factory with sawtooth roof
        d.rectangle([x0 + 8, y1 - 30, x1 - 8, y1 - 6], fill=(150, 90, 80))
        for i in range(4):
            sx = x0 + 8 + i * ((w - 16) // 4)
            d.polygon([(sx, y1 - 30), (sx + (w - 16) // 8, y1 - 42),
                       (sx + (w - 16) // 4, y1 - 30)], fill=(120, 70, 62))
        d.rectangle([x1 - 30, y1 - 52, x1 - 22, y1 - 30], fill=(110, 104, 96))
        # shirts on a line
        d.line([(x0 + 10, y1 - 48), (x1 - 10, y1 - 48)], fill=INK, width=1)
        for i, c in enumerate([(255, 255, 255), (220, 60, 60), (60, 110, 200)]):
            sx = x0 + 16 + i * 22
            d.rectangle([sx, y1 - 48, sx + 14, y1 - 34], fill=c, outline=INK)

    elif kind == "dow":
        _sky(d, box, (238, 240, 236), (250, 248, 242))
        # candlesticks
        vals = [(0.55, 0.7), (0.62, 0.78), (0.5, 0.66), (0.58, 0.74), (0.72, 0.86)]
        bw = (w - 30) // 5
        for i, (lo, hi) in enumerate(vals):
            bx = x0 + 14 + i * bw
            top = y0 + int(h * (1 - hi))
            bot = y0 + int(h * (1 - lo))
            c = (30, 130, 70) if hi > lo else (200, 50, 50)
            d.rectangle([bx, top, bx + bw - 8, bot], fill=c)
        # rebound arrow
        d.line([(x0 + 10, y1 - 12), (x1 - 40, y0 + 14)], fill=(30, 130, 70), width=3)
        d.polygon([(x1 - 40, y0 + 14), (x1 - 52, y0 + 16), (x1 - 42, y0 + 26)],
                  fill=(30, 130, 70))
        d.text((x0 + 8, y0 + 4), "50,183", font=F_SANSB(12), fill=(30, 100, 60))

    elif kind == "parliament":
        _sky(d, box, (214, 224, 232), (242, 238, 228))
        # columned building
        d.polygon([(cx - 34, y0 + 14), (cx, y0 + 2), (cx + 34, y0 + 14)], fill=(150, 140, 120))
        d.rectangle([x0 + 10, y1 - 26, x1 - 10, y1 - 6], fill=(170, 160, 138))
        for i in range(5):
            px = x0 + 16 + i * ((w - 32) // 5)
            d.rectangle([px, y0 + 16, px + 6, y1 - 26], fill=(230, 222, 200))
        # screen with check
        d.rectangle([x1 - 40, y0 + 8, x1 - 10, y0 + 26], fill=NAVY)
        d.line([(x1 - 36, y0 + 17), (x1 - 28, y0 + 23), (x1 - 14, y0 + 11)],
               fill=(255, 255, 255), width=2)

    else:  # generic: sky + skyline
        _sky(d, box, (210, 222, 230), (240, 236, 226))
        for bx, bw, bh in [(0.06, 0.18, 0.5), (0.28, 0.14, 0.65), (0.46, 0.2, 0.45),
                           (0.7, 0.16, 0.58)]:
            d.rectangle([x0 + w * bx, y1 - h * bh, x0 + w * (bx + bw), y1],
                        fill=(120, 130, 150))

# ---------------------------------------------------------------- content
# All stories verified as Wednesday 25 November 2026 (see v2 research file).
# Badge: OFFICIAL = government / official body; REPORTED = news agency;
# CLAIM = one-sided claim without independent confirmation.

HEROES = [
    dict(kind="tariff", badge="OFFICIAL", source="REUTERS · USTR",
         head="U.S. UNVEILS SECTION 301 TARIFFS ON 14 ECONOMIES",
         deck="USTR findings on 14 of 16 probes: China up to 20%, EU 15%, "
              "Japan, Korea, Taiwan and Switzerland 15%, Vietnam up to 35%, "
              "India 25%. Mexico and Norway exempt; hearings from 25 Jan 2027. "
              "Tariffs not yet in force."),
    dict(kind="chip", badge="REPORTED", source="WSJ · BARCHART",
         head="ASIAN CHIP STOCKS CRASH AT THE CLOSE",
         deck="Kospi −6.2% to 4,697.51, lowest since 13 Jan; Samsung −9.9%, "
              "SK Hynix −11.1%. Taiex −4.8%, Nikkei −2.8% (SoftBank −14.8%). "
              "Only India's Nifty rose, on AI-spending doubts and tariff threats."),
    dict(kind="rocket", badge="OFFICIAL", source="REUTERS",
         head="PAKISTAN'S FIRST ASTRONAUT DOCKS AT TIANGONG",
         deck="Long March 2F lifts off 00:18 UTC; Shenzhou-24 docks at Tiangong "
              "03:56 UTC. Muhammad Zeeshan Ali becomes the first Pakistani in "
              "orbit — and the first foreign visitor to the Chinese station."),
]

CARDS = [
    dict(kind="fire", badge="REPORTED",
         head="FUEL TANKER FIRE KILLS 31+ IN CAIRO",
         deck="Ring Road, El Warraq, 18:08 local. Tanker explodes; 31+ dead, "
              "21 injured, 27 vehicles destroyed."),
    dict(kind="mine", badge="REPORTED",
         head="9 DEAD, 17 TRAPPED IN FLOODED JAVA MINE",
         deck="Ciseureuh river floods a 100-m shaft at Bogor. 26 miners "
              "underground."),
    dict(kind="energy", badge="OFFICIAL",
         head="UK ENERGY CAP TO RISE 26% TO £2,166",
         deck="Ofgem: cap rises 26% (+£443) to £2,166 a year from 1 Jan. "
              "About 20m homes get £100."),
    dict(kind="port", badge="REPORTED",
         head="WEDNESDAY ROUND: STRIKES HIT HODEIDAH",
         deck="Coalition announces Wed-morning strikes on the port, Saada and "
              "Amran. Houthis threaten Jeddah."),
    dict(kind="tankersea", badge="CLAIM",
         head="IRGC CLAIMS TWO TANKERS HIT BY MINES",
         deck="IRGC navy says two tankers hit sea mines in Hormuz Wed morning. "
              "No independent confirmation."),
    dict(kind="gaza", badge="REPORTED",
         head="HAMAS SECURITY CHIEF KILLED AT DAWN",
         deck="Dawn strike kills Hamas security chief Col. Abu al-Awf, 47, "
              "with his wife and two daughters in Gaza."),
    dict(kind="gdp", badge="OFFICIAL",
         head="U.S. ECONOMY: GDP 4.3%, PCE 3.8%",
         deck="BEA, 13:30 UTC: Q3 GDP 4.3% annualised; Oct PCE +3.8% y/y; "
              "core PCE +3.3%."),
    dict(kind="refinery", badge="CLAIM",
         head="HOUTHIS CLAIM STRIKE ON RAS TANURA",
         deck="Houthis claim hits on Ras Tanura refinery and Riyadh. "
              "Coalition: 4 drones downed; no hit confirmed."),
    dict(kind="drone", badge="REPORTED",
         head="UKRAINIAN DRONES HIT TWO REFINERIES",
         deck="Drones hit Rosneft's Syzran and Kuibyshev refineries overnight; "
              "fires at both. 145+ drones downed."),
    dict(kind="garment", badge="REPORTED",
         head="GARMENT WAGE RISES TO 17,500 TAKA",
         deck="Bangladesh wage board agrees 12,500 → 17,500 taka a month from "
              "Dec; workers wanted 30,000."),
    dict(kind="dow", badge="REPORTED",
         head="DOW HOLDS ABOVE 50,000 AFTER 1,100-POINT SWING",
         deck="Dow closes 50,182.95 (+0.33%) after recovering from a "
              "1,100-point intraday slide."),
    dict(kind="parliament", badge="OFFICIAL",
         head="AUSTRALIA PASSES DIGITAL DUTY OF CARE",
         deck="Parliament passes Digital Duty of Care; fines up to 5% of "
              "global revenue or A$109.2m."),
]

# 29 numbered briefs — one line each (fitted to 2 lines max at render time).
BRIEFS = [
    "Netanyahu: judges suggest dropping Case 4000 — AG to review; not a ruling.",
    "Poland plans limited no-fly zone along Ukraine border; rules due late Dec.",
    "EU proposes Quantum Act + fund targeting up to €50bn (proposal, not committed).",
    "FCC clears SpaceX to deploy up to 1m 'Starmind' satellites for orbital AI data centres.",
    "RSF drone attack on Damazin kills 19 civilians, reported Wed (attack Tue night).",
    "UN peacekeepers evacuate 10 health workers from Ebola zone in Ituri, DR Congo.",
    "North Korea expels Swiss envoy Sylvain Astier; 48 hours to leave, office shut.",
    "Iowa: Army detonates ~5 tons of damaged lead azide; EPA monitors show zero lead in air.",
    "Athens 24-hour general strike: ~15,000 march; ferries halted; 32 flights cancelled.",
    "Eurostar wildcat strike cancels at least 6 Paris–London trains.",
    "Russia budget, reported Wed: defence ~$606bn over 3 years (Duma vote Tue).",
    "Paraná floods: toll reaches 6 in Wed count; 10,837 people affected.",
    "Mexico to send diplomatic note over U.S. refusal to extradite Gómez Mont.",
    "Duran Duran guitarist Andy Taylor dies at 65, announced Wed (died Mon).",
    "Cartagena: all supermarket hostages freed after day-long siege (began Tue).",
    "Australia–Solomon Islands treaty signed in Canberra; China pact to lapse in 2027.",
    "Ramaphosa wins court case: Farmgate panel report quashed.",
    "Australia CPI jumps to 4.9% y/y in October, above forecasts.",
    "Japan services PPI +4.2%, fastest since 1990.",
    "South Korea births +12.2% in September, 27th straight annual rise.",
    "Korea exports pass $1tn for the first time.",
    "India declared Naxal-free: LWE districts down from 126 to zero.",
    "Qatar and Canada hold first Strategic Dialogue in Ottawa.",
    "Zelenskyy: Ukraine needs €115bn in 2027 to hold on.",
    "Merz: Europe ready to negotiate with Russia in Abu Dhabi.",
    "Nigeria to sign digital services deal with five African nations.",
    "Kenya to recruit 20,000 teachers in 2026/27.",
    "UN 16 Days of Activism against gender-based violence begins (25 Nov–10 Dec).",
    "Delhi: Supreme Court to hear Delhi air-pollution case.",
]

STATS = [
    ("31+", "CAIRO DEAD"),
    ("+26%", "UK ENERGY CAP"),
    ("−6.2%", "KOSPI"),
    ("20%", "CHINA TARIFF"),
    ("4.3%", "U.S. GDP"),
    ("1ST", "PAKISTANI ASTRONAUT"),
]

REGIONS = ("ASIA-PACIFIC 11  ·  EUROPE 10  ·  AMERICAS 7  ·  MIDDLE EAST 6  ·  "
           "AFRICA 5  ·  OCEANIA 3  ·  GLOBAL 2  —  44 STORIES")

TIMELINE = [
    ("00:18", "Shenzhou-24 lifts off, Jiuquan"),
    ("03:56", "Docking at Tiangong"),
    ("06:30", "Kospi closes −6.2%"),
    ("13:30", "U.S. GDP / PCE released (BEA)"),
    ("15:00", "Iowa lead-azide blast (09:00 CT)"),
    ("16:08", "Cairo tanker fire (18:08 Egypt)"),
]

# (number, name, lon, lat, dx, dy) — dx/dy nudge pins apart where they cluster.
PINS = [
    (1, "Jiuquan", 98.5, 40.9, 0, 0),
    (2, "Seoul", 127.0, 37.6, 0, -10),
    (3, "Taipei", 121.6, 25.0, -10, 8),
    (4, "Tokyo", 139.7, 35.7, 10, -6),
    (5, "Cairo", 31.2, 30.0, 0, 0),
    (6, "Bogor", 106.8, -6.6, 0, 0),
    (7, "London", -0.1, 51.5, 0, 0),
    (8, "Hodeidah", 42.9, 14.8, -8, 8),
    (9, "Hormuz", 56.4, 26.9, 0, -10),
    (10, "Gaza", 34.5, 31.5, 12, 8),
    (11, "Samara", 50.1, 53.2, 0, 0),
    (12, "Washington", -77.0, 38.9, 0, 0),
]

DATE_CHECK = ("Huawei verdict (24 Nov) · Hodeidah Tue round (24 Nov) · Huang returns as "
              "Nvidia CEO (23–24 Nov) · Senegal AFCON restored (24 Nov) · PIF tower strike "
              "(24 Nov) · Miss Universe (24 Nov) · COP31 collapse (22 Nov) · Nvidia slide "
              "(24 Nov) · Sinner knee surgery (24 Nov) · Dow first close above 50,000 "
              "(24 Nov) · Russia budget vote (24 Nov) · Eisenkot–Lieberman pact (24 Nov) · "
              "'El Chapo Isidro' ruling (24 Nov) · UN femicide report (24 Nov) · Rocha "
              "Moya resignation (May 2026)")

SOURCES = ("SOURCES: REUTERS · AP · AFP · AL JAZEERA · XINHUA · CNN · WSJ · BEA · "
           "OFGEM · USTR · KCNA · UN NEWS · G1 · DEFESA CIVIL PARANÁ")


# ---------------------------------------------------------------- layout
def draw_hero(d, x, y, w, h, item):
    d.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=LINE)
    scene(d, item["kind"], (x + 1, y + 1, x + w - 1, y + 85))
    d.line([(x, y + 85), (x + w, y + 85)], fill=LINE, width=1)
    head_lines = fit_lines(d, item["head"], F_SERIF(15), w - 16, 2)
    para(d, x + 8, y + 90, head_lines, F_SERIF(15), INK, 17)
    deck_lines = fit_lines(d, item["deck"], F_SANS(11), w - 16, 5)
    para(d, x + 8, y + 128, deck_lines, F_SANS(11), (40, 40, 38), 13)
    badge(d, x + 8, y + h - 14, item["badge"])
    sf = F_SANS(8)
    sw = d.textlength(item["source"], font=sf)
    d.text((x + w - 8 - sw, y + h - 13), item["source"], font=sf, fill=MUTED)


def draw_card(d, x, y, w, h, item):
    d.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=LINE)
    scene(d, item["kind"], (x + 1, y + 1, x + w - 1, y + 45))
    badge(d, x + 5, y + 5, item["badge"])
    head_lines = fit_lines(d, item["head"], F_SANSB(10), w - 12, 2)
    para(d, x + 6, y + 49, head_lines, F_SANSB(10), INK, 12)
    deck_lines = fit_lines(d, item["deck"], F_SANS(10), w - 12, 4)
    para(d, x + 6, y + 75, deck_lines, F_SANS(10), (50, 50, 48), 11)

def draw_map(d, x0, y0, w, h):
    d.text((x0, y0), "WHERE IT HAPPENED — 12 PINNED STORIES",
           font=F_SANSB(10), fill=INK)
    d.line([(x0, y0 + 14), (x0 + w, y0 + 14)], fill=LINE, width=1)
    panel_y = y0 + 18
    panel_h = h - 38
    d.rectangle([x0, panel_y, x0 + w, panel_y + panel_h], fill=SEA)
    with open(os.path.join(HERE, "countries.geo.json")) as f:
        gj = json.load(f)
    s = min(w / 360.0, panel_h / 145.0)
    ox = x0 + (w - 360 * s) / 2
    oy = panel_y

    def P(lon, lat):
        return (ox + (lon + 180) * s, oy + (85 - lat) * s)

    for feat in gj["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            polys = [geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue
        for poly in polys:
            for ring in poly:
                pts = [P(lon, lat) for lon, lat in ring]
                d.polygon(pts, fill=LAND, outline=LAND_LINE)
    for num, _name, lon, lat, dx, dy in PINS:
        px, py = P(lon, lat)
        if dx or dy:
            d.line([(px, py), (px + dx, py + dy)], fill=RED, width=1)
            px, py = px + dx, py + dy
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=RED,
                  outline=(255, 255, 255))
        t = str(num)
        tw = d.textlength(t, font=F_SANSB(7))
        d.text((px - tw / 2, py - 5), t, font=F_SANSB(7), fill=(255, 255, 255))
    leg = F_SANS(8)
    d.text((x0, panel_y + panel_h + 4),
           "1 JIUQUAN · 2 SEOUL · 3 TAIPEI · 4 TOKYO · 5 CAIRO · 6 BOGOR",
           font=leg, fill=MUTED)
    d.text((x0, panel_y + panel_h + 14),
           "7 LONDON · 8 HODEIDAH · 9 HORMUZ · 10 GAZA · 11 SAMARA · 12 WASHINGTON",
           font=leg, fill=MUTED)


def draw_timeline(d, x0, y0, w, h):
    d.text((x0, y0), "THE DAY IN UTC", font=F_SANSB(10), fill=INK)
    d.line([(x0, y0 + 14), (x0 + w, y0 + 14)], fill=LINE, width=1)
    y = y0 + 20
    for t, ev in TIMELINE:
        d.text((x0, y), t, font=F_SANSB(11), fill=NAVY)
        d.text((x0 + 54, y), ev, font=F_SANS(10), fill=INK)
        y += 17


def draw_briefs(d, x0, y0):
    d.text((x0, y0), "ALSO ON WEDNESDAY 25 NOVEMBER — 29 MORE STORIES",
           font=F_SANSB(11), fill=INK)
    y_top = y0 + 20
    for ci in range(3):
        cx = 16 + ci * 334
        col = BRIEFS[ci * 10:(ci + 1) * 10]
        y = y_top
        for bi, text in enumerate(col):
            num = "B%d" % (ci * 10 + bi + 1)
            d.text((cx, y), num, font=F_SANSB(10), fill=RED)
            lines = fit_lines(d, text, F_SANS(10), 322 - 30, 2)
            para(d, cx + 28, y, lines, F_SANS(10), INK, 9.5)
            y += 19


def draw_footer(d, y):
    label = "DATE CHECK — "
    lf = F_SANSB(9)
    lw = d.textlength(label, font=lf)
    lines = fit_lines(d, DATE_CHECK, F_SANS(8), 992 - lw - 4, 3)
    d.text((16, y), label, font=lf, fill=RED)
    para(d, 16 + lw + 4, y, lines, F_SANS(8), (60, 60, 56), 10)
    y2 = y + len(lines) * 10 + 4
    d.text((16, y2), SOURCES, font=F_SANS(8), fill=MUTED)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead
    title = "THE WORLD IN ONE DAY"
    tf = F_SERIF(28)
    tw = d.textlength(title, font=tf)
    d.text(((W - tw) / 2, 8), title, font=tf, fill=INK)
    sub = "WEDNESDAY · 25 NOVEMBER 2026 · 44 STORIES FROM 7 REGIONS"
    sf = F_SANSB(12)
    sw = d.textlength(sub, font=sf)
    d.text(((W - sw) / 2, 42), sub, font=sf, fill=(60, 60, 56))
    d.line([(16, 58), (1008, 58)], fill=INK, width=2)

    # ---- red kicker with 3 leads
    d.rectangle([16, 60, 1008, 82], fill=RED)
    kick = "U.S. TARIFFS HIT 14 ECONOMIES    ·    KOSPI −6.2%    ·    " \
           "PAKISTAN'S FIRST ASTRONAUT IN ORBIT"
    kf = F_SANSB(12)
    kw = d.textlength(kick, font=kf)
    d.text(((W - kw) / 2, 67), kick, font=kf, fill=(255, 255, 255))

    # ---- stat strip
    d.rectangle([16, 86, 1008, 122], fill=NAVY)
    cell = 992 / 6
    for i, (num, lab) in enumerate(STATS):
        cx = 16 + i * cell
        nf = F_SANSB(16)
        nw = d.textlength(num, font=nf)
        d.text((cx + (cell - nw) / 2, 90), num, font=nf, fill=(255, 255, 255))
        lf2 = F_SANS(8)
        lw2 = d.textlength(lab, font=lf2)
        d.text((cx + (cell - lw2) / 2, 110), lab, font=lf2, fill=GOLD)

    # ---- region bar
    d.line([(16, 126), (1008, 126)], fill=LINE, width=1)
    rf = F_SANSB(11)
    rw = d.textlength(REGIONS, font=rf)
    d.text(((W - rw) / 2, 131), REGIONS, font=rf, fill=INK)
    d.line([(16, 146), (1008, 146)], fill=LINE, width=1)

    # ---- heroes: 3 columns
    for i, item in enumerate(HEROES):
        draw_hero(d, 16 + i * 334, 150, 322, 210, item)

    # ---- cards: 6 columns x 2 rows
    for i, item in enumerate(CARDS):
        col, row = i % 6, i // 6
        draw_card(d, 16 + col * 167, 366 + row * 132, 157, 126, item)

    # ---- map + timeline
    draw_map(d, 16, 630, 560, 126)
    draw_timeline(d, 584, 630, 424, 126)

    # ---- briefs
    draw_briefs(d, 16, 762)

    # ---- footer
    draw_footer(d, 976)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or HERE
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    img.save(out_path, format="PNG")


if __name__ == "__main__":
    main()
