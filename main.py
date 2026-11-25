#!/usr/bin/env python3
"""The World in One Day -- Wednesday 25 November 2026.

A broadsheet front page drawn entirely in code (Python standard library
only) and written to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
No network, no local imports, no randomness: two runs write identical bytes.

Layout (1024x1024): kicker strip, masthead, subhead, region strip, numbers
row, three hero stories with code-drawn scenes, eleven illustrated cards,
a world map with numbered pins, a numbered brief list, a DATE CHECK footer
and a sources footer. Every story happened, or was first reported, on
Wednesday 25 November 2026, as the named outlets reported it.
"""
import json
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)      # newsprint cream
PAPER2 = (242, 236, 220)     # slightly darker cream
INK = (24, 24, 24)           # near-black text
NAVY = (18, 32, 61)          # kicker strip / hero tags
NAVY2 = (30, 48, 92)
RED = (172, 32, 28)          # accent red
REDBG = (246, 226, 222)      # date-check background
RULE = (120, 110, 92)        # thin rules
LIGHT = (214, 204, 184)      # card borders / dividers
LAND = (216, 205, 180)       # map land fill
LANDLINE = (150, 138, 110)   # map country outlines
SEA = (233, 228, 214)        # map ocean
WHITE = (255, 255, 255)
SKY = (16, 28, 64)           # rocket scene sky
SKY2 = (36, 58, 110)
SEA2 = (38, 84, 124)         # port scene sea
STEEL = (70, 78, 92)
GOLD = (212, 160, 44)
GREEN = (46, 125, 60)
ORANGE = (224, 122, 32)

# ---------------------------------------------------------------- PNG out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(rgb, w, h):
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(rgb[y * w * 3:(y + 1) * w * 3])
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.fill_rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c):
        x = 0
        y = r
        d = 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def poly(self, pts, c):
        """Filled polygon, even-odd scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, min(ys))
        y1 = min(self.h - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, y0p = pts[i]
                x1, y1p = pts[(i + 1) % n]
                if (y0p <= y < y1p) or (y1p <= y < y0p):
                    if y1p != y0p:
                        x = x0 + (y - y0p) * (x1 - x0) / (y1p - y0p)
                        xs.append(x)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = max(0, int(xs[i] + 0.5))
                xb = min(self.w - 1, int(xs[i + 1] + 0.5))
                if xb >= xa:
                    self.fill_rect(xa, y, xb - xa + 1, 1, c)

    def polyline(self, pts, c):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 cells, '#' = ink. Hand-built for this page.
FONT = {
'A': (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
'B': ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
'C': (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
'D': ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
'E': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
'F': ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
'G': (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
'H': ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
'I': (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
'J': ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
'K': ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
'L': ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
'M': ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
'N': ("#   #", "##  #", "##  #", "# # #", "#  ##", "#  ##", "#   #"),
'O': (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
'P': ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
'Q': (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
'R': ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
'S': (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
'T': ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
'U': ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
'V': ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
'W': ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
'X': ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
'Y': ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
'Z': ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
'0': (" ### ", "#  ##", "# # #", "##  #", "#   #", "#   #", " ### "),
'1': ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
'2': (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
'3': ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
'4': ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
'5': ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
'6': (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
'7': ("#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "  #  "),
'8': (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
'9': (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
}

FONT.update({
'a': ("     ", "     ", " ### ", "    #", " ####", "#   #", " ####"),
'b': ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#### "),
'c': ("     ", "     ", " ####", "#    ", "#    ", "#    ", " ####"),
'd': ("    #", "    #", " ####", "#   #", "#   #", "#   #", " ####"),
'e': ("     ", "     ", " ### ", "#   #", "#####", "#    ", " ### "),
'f': ("  ## ", " #  #", " #   ", "###  ", " #   ", " #   ", " #   "),
'g': ("     ", "     ", " ####", "#   #", "#   #", " ####", "    #"),
'h': ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#   #"),
'i': ("  #  ", "     ", " ##  ", "  #  ", "  #  ", "  #  ", " ### "),
'j': ("   # ", "     ", "  ## ", "   # ", "   # ", "   # ", " ##  "),
'k': ("#    ", "#    ", "#  # ", "# #  ", "##   ", "# #  ", "#  # "),
'l': (" ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
'm': ("     ", "     ", "## # ", "# # #", "# # #", "# # #", "# # #"),
'n': ("     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #"),
'o': ("     ", "     ", " ### ", "#   #", "#   #", "#   #", " ### "),
'p': ("     ", "     ", "#### ", "#   #", "#   #", "#### ", "#    "),
'q': ("     ", "     ", " ####", "#   #", "#   #", " ####", "    #"),
'r': ("     ", "     ", "# ## ", "##  #", "#    ", "#    ", "#    "),
's': ("     ", "     ", " ####", "#    ", " ### ", "    #", "#### "),
't': (" #   ", " #   ", "###  ", " #   ", " #   ", " #   ", "  ## "),
'u': ("     ", "     ", "#   #", "#   #", "#   #", "#  ##", " ## #"),
'v': ("     ", "     ", "#   #", "#   #", "#   #", " # # ", "  #  "),
'w': ("     ", "     ", "#   #", "# # #", "# # #", "# # #", " # # "),
'x': ("     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"),
'y': ("     ", "     ", "#   #", "#   #", "#   #", " ####", "    #"),
'z': ("     ", "     ", "#####", "   # ", "  #  ", " #   ", "#####"),
' ': ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
'.': ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
',': ("     ", "     ", "     ", "     ", "     ", " ##  ", " #   "),
':': ("     ", "     ", " ##  ", " ##  ", "     ", " ##  ", " ##  "),
';': ("     ", "     ", " ##  ", " ##  ", "     ", " ##  ", " #   "),
'!': ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
'?': (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
"'": ("  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "),
'"': (" # # ", " # # ", "     ", "     ", "     ", "     ", "     "),
'(': ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
')': (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
'-': ("     ", "     ", "     ", " ### ", "     ", "     ", "     "),
'/': ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
'%': ("##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"),
'+': ("     ", "     ", "  #  ", " ### ", "  #  ", "     ", "     "),
'$': ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
'&': (" ##  ", "#  # ", "# #  ", " #   ", "# # #", "#  # ", " ## #"),
'=': ("     ", "     ", "#### ", "     ", "#### ", "     ", "     "),
'#': (" # # ", " # # ", "#####", " # # ", "#####", " # # ", " # # "),
'_': ("     ", "     ", "     ", "     ", "     ", "     ", "#####"),
'<': ("   # ", "  #  ", " #   ", "#    ", " #   ", "  #  ", "   # "),
'>': (" #   ", "  #  ", "   # ", "    #", "   # ", "  #  ", " #   "),
'[': (" ### ", " #   ", " #   ", " #   ", " #   ", " #   ", " ### "),
']': (" ### ", "   # ", "   # ", "   # ", "   # ", "   # ", " ### "),
'*': ("     ", " # # ", "  #  ", "#####", "  #  ", " # # ", "     "),
'~': ("     ", "     ", " ## #", "#  ##", "     ", "     ", "     "),
'^': ("  #  ", " # # ", "     ", "     ", "     ", "     ", "     "),
'`': ("  #  ", " #   ", "     ", "     ", "     ", "     ", "     "),
'|': ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
'\\': ("#    ", "#    ", " #   ", "  #  ", "   # ", "    #", "    #"),
'@': (" ### ", "#   #", "# ###", "# # #", "# ###", "#    ", " ### "),
'{': ("   ##", "  #  ", "  #  ", " ##  ", "  #  ", "  #  ", "   ##"),
'}': ("##   ", "  #  ", "  #  ", "  ## ", "  #  ", "  #  ", "##   "),
# middle dot (word separator) and em dash
'\u00b7': ("     ", "     ", "     ", "  #  ", "     ", "     ", "     "),
'\u2014': ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
'\u2013': ("     ", "     ", "     ", " ### ", "     ", "     ", "     "),
'\u00b0': (" ##  ", "#  # ", " ##  ", "     ", "     ", "     ", "     "),
})


# ---------------------------------------------------------------- text
def text_w(s, scale, bold=False):
    w = 0
    for ch in s:
        w += 6 * scale + (1 if bold else 0)
    return max(0, w - scale)


def draw_text(cv, x, y, s, scale, color, bold=False, align="left"):
    if align == "center":
        x -= text_w(s, scale, bold) // 2
    elif align == "right":
        x -= text_w(s, scale, bold)
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            g = FONT["?"]
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "#":
                    cv.fill_rect(cx + c * scale, y + r * scale, scale, scale, color)
                    if bold:
                        cv.fill_rect(cx + c * scale + 1, y + r * scale, scale, scale, color)
        cx += 6 * scale + (1 if bold else 0)
    return cx


def wrap_text(s, max_w, scale, bold=False):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    lines = []
    for chunk in s.split("\n"):
        words = chunk.split(" ")
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if text_w(trial, scale, bold) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
    return lines


def draw_para(cv, x, y, s, max_w, scale, color, bold=False, leading=None, max_lines=None):
    lines = wrap_text(s, max_w, scale, bold)
    if max_lines is not None:
        lines = lines[:max_lines]
    lh = 7 * scale + (leading if leading is not None else max(1, scale))
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * lh, ln, scale, color, bold)
    return y + len(lines) * lh


# ---------------------------------------------------------------- scenes
# Every illustration is drawn in code: rectangles, discs, triangles, lines.
def scene_rocket(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + h - 26, w, 26, (10, 18, 44))
    for sx, sy, r in ((0.12, 0.16, 2), (0.30, 0.08, 1), (0.48, 0.22, 2),
                      (0.66, 0.10, 1), (0.82, 0.18, 2), (0.94, 0.07, 1),
                      (0.22, 0.30, 1), (0.58, 0.32, 1), (0.74, 0.28, 1)):
        cv.disc(x + int(w * sx), y + int(h * sy), r, WHITE)
    # launch tower
    tx = x + int(w * 0.30)
    cv.fill_rect(tx, y + 22, 5, h - 48, STEEL)
    cv.fill_rect(tx - 8, y + 30, 21, 3, STEEL)
    cv.fill_rect(tx - 8, y + 48, 21, 3, STEEL)
    # rocket body
    rx = x + int(w * 0.56)
    rw = 26
    cv.fill_rect(rx, y + 14, rw, 62, WHITE)
    cv.poly([(rx, y + 14), (rx + rw // 2, y + 2), (rx + rw, y + 14)], RED)
    cv.fill_rect(rx, y + 40, rw, 4, RED)
    cv.fill_rect(rx - 8, y + 62, 8, 16, RED)
    cv.fill_rect(rx + rw, y + 62, 8, 16, RED)
    # flame + smoke
    cv.poly([(rx + 4, y + 78), (rx + rw // 2, y + h - 26), (rx + rw - 4, y + 78)], ORANGE)
    cv.poly([(rx + 9, y + 78), (rx + rw // 2, y + h - 34), (rx + rw - 9, y + 78)], GOLD)
    for sx, sy, r in ((0.42, 0.86, 9), (0.62, 0.90, 11), (0.80, 0.84, 8), (0.30, 0.92, 7)):
        cv.disc(x + int(w * sx), y + int(h * sy), r, (168, 172, 184))
    cv.fill_rect(x, y + h - 4, w, 4, (8, 14, 36))


def scene_port(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (224, 200, 160))
    cv.fill_rect(x, y + int(h * 0.62), w, h - int(h * 0.62), SEA2)
    # sky glow + smoke columns
    cv.disc(x + int(w * 0.72), y + int(h * 0.30), 16, (240, 150, 60))
    for sx, sw in ((0.30, 14), (0.52, 18), (0.78, 12)):
        bx = x + int(w * sx)
        for i, r in enumerate((sw, sw - 3, sw - 6)):
            cv.disc(bx + (i - 1) * 4, y + 16 + i * 10, r, (120, 118, 112))
    # cranes
    for cx in (0.14, 0.44):
        bx = x + int(w * cx)
        cv.fill_rect(bx, y + 18, 5, int(h * 0.48), STEEL)
        cv.fill_rect(bx, y + 18, 52, 5, STEEL)
        cv.line(bx + 52, y + 18, bx + 34, y + 40, STEEL)
        cv.line(bx + 5, y + 23, bx + 5, y + 52, STEEL)
        cv.fill_rect(bx + 2, y + 52, 8, 7, GOLD)
    # containers
    cols = (RED, GOLD, GREEN, NAVY2, (200, 90, 40))
    for i, cc in enumerate(cols):
        cv.fill_rect(x + 8 + i * 46, y + int(h * 0.60), 42, 16, cc)
        cv.rect(x + 8 + i * 46, y + int(h * 0.60), 42, 16, INK)
    # water lines
    for wy in (0.72, 0.82, 0.92):
        cv.fill_rect(x + 10, y + int(h * wy), w - 30, 2, (140, 180, 205))


def scene_chart(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (18, 24, 40))
    # grid
    for gy in range(1, 4):
        cv.fill_rect(x + 8, y + gy * h // 4, w - 16, 1, (52, 62, 92))
    # falling bars
    vals = (0.92, 0.86, 0.88, 0.74, 0.66, 0.70, 0.55, 0.44, 0.48, 0.34, 0.24, 0.16)
    bw = (w - 24) // len(vals)
    for i, v in enumerate(vals):
        bh = int(h * 0.62 * v)
        cv.fill_rect(x + 12 + i * bw, y + h - 12 - bh, bw - 3, bh, RED)
    # trend line
    pts = []
    for i, v in enumerate(vals):
        pts.append((x + 12 + i * bw + bw // 2, y + h - 14 - int(h * 0.62 * v)))
    cv.polyline(pts, GOLD)
    for px, py in pts:
        cv.disc(px, py, 2, GOLD)
    cv.fill_rect(x, y + h - 12, w, 2, (120, 130, 160))


def scene_flags(cv, x, y, w, h, c1, c2):
    """Two flags on poles (treaty / dialogue scenes)."""
    cv.fill_rect(x, y, w, h, (226, 220, 200))
    cv.fill_rect(x, y + h - 10, w, 10, (150, 138, 110))
    for i, cc in enumerate((c1, c2)):
        px = x + int(w * (0.22 + 0.42 * i))
        cv.fill_rect(px, y + 6, 3, h - 16, STEEL)
        cv.fill_rect(px + 3, y + 6, 62, 26, cc)
        cv.fill_rect(px + 3, y + 6, 62, 5, WHITE)
        cv.disc(px + 34, y + 19, 5, GOLD if i == 0 else WHITE)


def scene_store(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (210, 196, 168))
    cv.fill_rect(x + 8, y + int(h * 0.28), w - 16, h - int(h * 0.28) - 6, (240, 236, 224))
    cv.fill_rect(x + 8, y + int(h * 0.28), w - 16, 8, NAVY)
    wy = y + int(h * 0.52)
    wh = int(h * 0.22)
    for i in range(3):
        cv.fill_rect(x + 14 + i * 34, wy, 24, wh, (140, 180, 210))
    cv.fill_rect(x + 8, y + h - 6, w - 16, 3, INK)


def scene_skyline(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (196, 214, 232))
    base = y + h - 6
    specs = ((0.06, 0.38), (0.24, 0.52), (0.44, 0.44), (0.62, 0.60), (0.80, 0.36))
    tops = []
    for bx, bh in specs:
        px = x + int(w * bx)
        ph = int(h * bh)
        cv.fill_rect(px, base - ph, 30, ph, (44, 54, 78) if bx == 0.62 else (70, 80, 100))
        for wy in range(base - ph + 5, base - 3, 8):
            cv.fill_rect(px + 5, wy, 20, 3, GOLD)
        tops.append((px, base - ph))
    # red flag on the tallest tower
    fx, ft = tops[3]
    cv.fill_rect(fx + 15, ft - 8, 2, 8, INK)
    cv.poly([(fx + 17, ft - 8), (fx + 29, ft - 5), (fx + 17, ft - 2)], RED)
    cv.fill_rect(x, base, w, 6, (90, 96, 110))


def scene_court(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (228, 222, 204))
    cv.poly([(x + 8, y + 16), (x + w // 2, y + 2), (x + w - 8, y + 16)], NAVY2)
    cv.fill_rect(x + 8, y + 16, w - 16, 5, NAVY2)
    for i in range(4):
        px = x + 16 + i * ((w - 32) // 3)
        cv.fill_rect(px, y + 21, 7, h - 34, WHITE)
        cv.rect(px, y + 21, 7, h - 34, INK)
    cv.fill_rect(x + 8, y + h - 13, w - 16, 6, NAVY2)
    cv.fill_rect(x + w // 2 - 22, y + h - 8, 44, 4, INK)


def scene_bars_up(cv, x, y, w, h, color=RED):
    cv.fill_rect(x, y, w, h, (232, 226, 210))
    vals = (0.30, 0.42, 0.38, 0.55, 0.62, 0.78, 0.92)
    bw = (w - 20) // len(vals)
    for i, v in enumerate(vals):
        bh = int((h - 16) * v)
        cv.fill_rect(x + 10 + i * bw, y + h - 8 - bh, bw - 3, bh, color)
    cv.fill_rect(x + 6, y + h - 8, w - 12, 2, INK)


def scene_line_up(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (232, 226, 210))
    for gy in range(1, 4):
        cv.fill_rect(x + 8, y + gy * h // 4, w - 16, 1, LIGHT)
    pts = [(x + 12 + i * (w - 24) // 6, y + h - 10 - int((h - 20) * v))
           for i, v in enumerate((0.20, 0.28, 0.26, 0.42, 0.55, 0.72, 0.90))]
    cv.polyline(pts, RED)
    for px, py in pts:
        cv.disc(px, py, 2, RED)
    cv.fill_rect(x + 6, y + h - 8, w - 12, 2, INK)


def scene_scales(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (228, 222, 204))
    cx = x + w // 2
    cv.fill_rect(cx - 2, y + 6, 4, h - 18, INK)
    cv.fill_rect(cx - 22, y + 8, 44, 3, INK)
    for sgn in (-1, 1):
        px = cx + sgn * 20
        cv.line(px, y + 11, px - 6, y + 24, INK)
        cv.line(px, y + 11, px + 6, y + 24, INK)
        cv.poly([(px - 8, y + 24), (px + 8, y + 24), (px, y + 32)], GOLD)
    cv.fill_rect(cx - 12, y + h - 12, 24, 5, INK)


def scene_refinery(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (24, 26, 44))
    cv.disc(x + int(w * 0.78), y + 10, 7, GOLD)
    base = y + h - 6
    for bx, bh in ((0.10, 0.42), (0.30, 0.55), (0.52, 0.34)):
        px = x + int(w * bx)
        ph = int(h * bh)
        cv.fill_rect(px, base - ph, 14, ph, STEEL)
        cv.fill_rect(px - 2, base - ph - 3, 18, 3, STEEL)
    # flare stack
    fx = x + int(w * 0.66)
    cv.fill_rect(fx, base - 16, 22, 16, (120, 60, 40))
    cv.poly([(fx + 2, base - 16), (fx + 11, base - 28), (fx + 20, base - 16)], ORANGE)
    cv.disc(fx + 11, base - 31, 4, GOLD)
    cv.fill_rect(x, base, w, 6, (12, 14, 26))
    # drone
    dx, dy = x + int(w * 0.30), y + 8
    cv.fill_rect(dx - 6, dy, 12, 4, WHITE)
    cv.fill_rect(dx - 12, dy - 2, 5, 2, WHITE)
    cv.fill_rect(dx + 7, dy - 2, 5, 2, WHITE)


def scene_check(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (214, 228, 206))
    pts = [(x + 10, y + h - 12), (x + 10, y + int(h * 0.55)), (x + w // 2, y + 8),
           (x + w - 10, y + int(h * 0.55)), (x + w - 10, y + h - 12)]
    cv.poly(pts, (120, 150, 110))
    cv.fill_rect(x + 10, y + h - 12, w - 20, 8, (90, 110, 84))
    cv.line(x + int(w * 0.30), y + int(h * 0.58), x + int(w * 0.44), y + int(h * 0.78), WHITE)
    cv.line(x + int(w * 0.44), y + int(h * 0.78), x + int(w * 0.72), y + int(h * 0.30), WHITE)
    cv.line(x + int(w * 0.30), y + int(h * 0.58) + 2, x + int(w * 0.44), y + int(h * 0.78) + 2, WHITE)
    cv.line(x + int(w * 0.44), y + int(h * 0.78) + 2, x + int(w * 0.72), y + int(h * 0.30) + 2, WHITE)


def scene_baby(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, (232, 226, 210))
    vals = (0.25, 0.34, 0.32, 0.46, 0.55, 0.66, 0.84)
    bw = (w - 20) // len(vals)
    for i, v in enumerate(vals):
        bh = int((h - 18) * v)
        cv.fill_rect(x + 10 + i * bw, y + h - 8 - bh, bw - 3, bh, GREEN)
    cv.fill_rect(x + 6, y + h - 8, w - 12, 2, INK)
    cx = x + w - 26
    cy = y + 12
    cv.disc(cx, cy, 7, (244, 200, 170))
    cv.fill_rect(cx - 8, cy + 8, 16, 10, (120, 170, 220))


# ---------------------------------------------------------------- map
def load_geo():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "countries.geo.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    polys = []
    for feat in data.get("features", []):
        geom = feat.get("geometry") or {}
        gtype = geom.get("type")
        coords = geom.get("coordinates") or []
        if gtype == "Polygon":
            polys.append(coords)
        elif gtype == "MultiPolygon":
            polys.extend(coords)
    return polys


def _split_ring(ring):
    """Split a lon/lat ring wherever it jumps across the antimeridian."""
    parts = [[]]
    prev = None
    for lon, lat in ring:
        if prev is not None and abs(lon - prev) > 180:
            parts.append([])
        parts[-1].append((lon, lat))
        prev = lon
    return [p for p in parts if len(p) >= 2]


def draw_map(cv, x, y, w, h, pins):
    """Equirectangular world map (lon -180..180, lat 84..-58) with pins."""
    lat_top, lat_bot = 84.0, -58.0

    def proj(lon, lat):
        px = x + (lon + 180.0) / 360.0 * w
        py = y + (lat_top - lat) / (lat_top - lat_bot) * h
        return (int(px + 0.5), int(py + 0.5))

    cv.fill_rect(x, y, w, h, SEA)
    try:
        polys = load_geo()
    except Exception:
        polys = []
    for poly in polys:
        for ring in poly:
            lats = [p[1] for p in ring]
            if not lats or max(lats) < lat_bot:
                continue
            for part in _split_ring(ring):
                pts = []
                for lon, lat in part:
                    px, py = proj(lon, lat)
                    px = min(max(px, x), x + w - 1)
                    py = min(max(py, y), y + h - 1)
                    pts.append((px, py))
                if len(pts) >= 3:
                    cv.poly(pts, LAND)
                    cv.polyline(pts + [pts[0]], LANDLINE)
    cv.rect(x, y, w, h, RULE)
    for num, lon, lat in pins:
        px, py = proj(lon, lat)
        cv.disc(px, py, 7, RED)
        cv.ring(px, py, 7, WHITE)
        label = str(num)
        tw = text_w(label, 1, True)
        draw_text(cv, px - tw // 2, py - 3, label, 1, WHITE, True)


# ---------------------------------------------------------------- stories
# All 36 stories happened, or were first reported, on Wednesday 25 Nov 2026.
HEROES = [
    dict(num=1, region="ASIA-PACIFIC", scene="rocket",
         head="Shenzhou-24 lifts off with Pakistan's first astronaut",
         deck="Long March 2F launches from Jiuquan at 00:18 UTC; Tang Hongbo, Wu Yi and Muhammad Zeeshan Ali — the first Pakistani in orbit — dock at Tiangong the same day.",
         src="REUTERS", badge="CONFIRMED"),
    dict(num=2, region="MIDDLE EAST", scene="port",
         head="Saudi-led coalition pounds Hodeidah port",
         deck="Strikes hit Houthi targets in Hodeidah, Saada and Amran after Houthis threaten Jeddah and all Saudi Red Sea ports; four drones downed over Ras Tanura.",
         src="REUTERS", badge="CONFIRMED"),
    dict(num=3, region="ASIA-PACIFIC", scene="chart",
         head="Asia's chip rout: Nikkei -3.5%, Kospi -5.5%",
         deck="Taiex -7.6%, SoftBank -16%, Ibiden -17.5%, Samsung -9%, TSMC -6.3% as Tuesday's AI rebound collapses on tariff threats and AI-spending doubts.",
         src="REUTERS", badge="CONFIRMED"),
]

CARDS = [
    dict(num=4, region="OCEANIA", scene="flags1",
         head="Australia signs historic pact with Solomon Islands",
         deck="Canberra is Honiara's primary security partner; China pact not renewed.",
         src="PM.GOV.AU · REUTERS", badge="OFFICIAL"),
    dict(num=5, region="AMERICAS", scene="store",
         head="All Cartagena supermarket hostages freed",
         deck="Colombian forces storm the Exito store, ending a day-long siege.",
         src="REUTERS / AFP", badge="CONFIRMED"),
    dict(num=6, region="ASIA-PACIFIC", scene="skyline",
         head="Shanghai pledges loyalty as purge reaches party boss",
         deck="City leaders vow absolute loyalty after Chen Jining is investigated.",
         src="REUTERS", badge="CONFIRMED"),
    dict(num=7, region="AMERICAS", scene="court",
         head="Huawei to appeal; sentencing set for 14 September 2027",
         deck="Firm welcomes RICO acquittal; lawyer: 'We fully expect to appeal.'",
         src="CYBERNEWS", badge="REPORTED"),
    dict(num=8, region="OCEANIA", scene="bars",
         head="Australia inflation jumps to 4.9%",
         deck="October CPI beats forecasts; housing +6.4%, electricity +25.2%.",
         src="ABS", badge="OFFICIAL"),
    dict(num=9, region="ASIA-PACIFIC", scene="lineup",
         head="Japan services inflation hits 36-year high",
         deck="Services PPI +4.2%, fastest since 1990; BOJ hike odds rise.",
         src="REUTERS", badge="CONFIRMED"),
    dict(num=10, region="AFRICA", scene="scales",
         head="Ramaphosa wins court case over Farmgate report",
         deck="High Court sets aside the Section 89 panel report on Phala Phala.",
         src="REUTERS", badge="CONFIRMED"),
    dict(num=11, region="EUROPE", scene="refinery",
         head="Ukrainian drones hit Samara refineries overnight",
         deck="Strikes spark blasts and fires near oil facilities in Samara.",
         src="H.UA", badge="REPORTED"),
    dict(num=12, region="AMERICAS", scene="flags2",
         head="Qatar and Canada hold first strategic dialogue",
         deck="Ottawa talks yield deals on Afghanistan, investment, museums.",
         src="QNA", badge="REPORTED"),
    dict(num=13, region="ASIA-PACIFIC", scene="check",
         head="India declares itself Naxal-free",
         deck="Left-wing extremism districts fall from 126 in 2014 to zero.",
         src="SEATBEAT", badge="REPORTED"),
    dict(num=14, region="ASIA-PACIFIC", scene="baby",
         head="South Korea births jump 12.2%",
         deck="September births rise a 27th straight month; fertility 0.90.",
         src="YONHAP", badge="CONFIRMED"),
]

# (number, one-line brief) — 22 briefs, numbered 15..36.
BRIEFS = [
    (15, "Pokrovsk: 203 clashes in a day; front's hottest sector."),
    (16, "South Lebanon: Israeli artillery hits seven villages."),
    (17, "New Zealand: $11.6m seized in Operation Scuba raids."),
    (18, "Wellington: RNZ reports a suspected cyber breach."),
    (19, "Auckland: NZ's best Miss Universe result since 1983."),
    (20, "Delhi: India launches gender campaign Nayi Chetna 5.0."),
    (21, "Delhi: court refuses to intervene on Kartarpur closure."),
    (22, "Berlin: Merz: Europe ready to negotiate in Abu Dhabi."),
    (23, "Kyiv: Zelenskyy says Ukraine needs EUR 115bn in 2027."),
    (24, "Canada: astronaut's wife gives birth; he is in orbit."),
    (25, "Seoul: consumer-goods exports hit record $28.65bn."),
    (26, "Seoul: ambassador to China called in slush-fund probe."),
    (27, "Seoul: Korea, UN agree peacekeeping working group."),
    (28, "Abuja: Nigeria to sign digital deal with five states."),
    (29, "Nairobi: Kenya to hire 20,000 teachers."),
    (30, "Nairobi: city launches 16 Days of Activism campaign."),
    (31, "UN: day to end violence against women begins."),
    (32, "Delhi: top court to hear Delhi air pollution case."),
    (33, "Seoul: 46.7% of users cannot find cancel button."),
    (34, "Seoul: unions demand retirement age rise to 65."),
    (35, "Pretoria: intel chief testifies behind closed doors."),
    (36, "Seoul: Kim Keon Hee final verdict set for 3 December."),
]

NUMBERS = [
    ("00:18", "SHENZHOU-24 LIFTS", "OFF, 00:18 UTC"),
    ("-7.6%", "TAIWAN STOCKS", "(TAIEX)"),
    ("-16%", "SOFTBANK", "SHARES"),
    ("4.9%", "AUSTRALIA CPI,", "OCTOBER"),
    ("+12.2%", "SOUTH KOREA BIRTHS,", "SEPTEMBER"),
    ("20,000", "TEACHERS TO BE HIRED,", "KENYA"),
]

# (story number, longitude, latitude)
PINS = [
    (1, 100.29, 40.96), (2, 42.95, 14.80), (3, 130.0, 33.0),
    (4, 149.13, -35.28), (5, -75.51, 10.40), (6, 121.47, 31.23),
    (7, -74.01, 40.71), (10, 28.19, -25.75), (11, 50.15, 53.20),
    (12, -75.70, 45.42), (13, 77.21, 28.61),
]

BADGE_COLOR = {"CONFIRMED": GREEN, "OFFICIAL": NAVY2, "REPORTED": RED}
SCENES = {
    "rocket": scene_rocket, "port": scene_port, "chart": scene_chart,
    "store": scene_store, "skyline": scene_skyline, "court": scene_court,
    "bars": scene_bars_up, "lineup": scene_line_up, "scales": scene_scales,
    "refinery": scene_refinery, "check": scene_check, "baby": scene_baby,
}


SCENES["flags1"] = lambda cv, x, y, w, h: scene_flags(cv, x, y, w, h, (0, 40, 110), (0, 90, 60))
SCENES["flags2"] = lambda cv, x, y, w, h: scene_flags(cv, x, y, w, h, (140, 20, 50), (200, 30, 30))


# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)

    # kicker strip
    cv.fill_rect(0, 0, W, 22, NAVY)
    draw_text(cv, 12, 4, "THE WORLD IN ONE DAY", 2, WHITE, True)
    draw_text(cv, 1012, 4, "EVERY STORY DATED WEDNESDAY 25 NOV", 2, WHITE, True, "right")

    # masthead
    draw_text(cv, 512, 26, "Wednesday 25 November 2026", 5, INK, True, "center")
    cv.hline(12, 66, 1000, RULE)
    cv.hline(12, 68, 1000, RULE)

    # subhead
    draw_text(cv, 512, 74, "Shenzhou-24 lifts off \u00b7 Saudi strikes Hodeidah \u00b7 Asia's chip rout",
              2, RED, False, "center")
    cv.hline(12, 92, 1000, RULE)

    # region strip + honesty note
    draw_text(cv, 512, 97,
              "36 STORIES \u00b7 ALL FROM WEDNESDAY 25 NOV \u00b7 ASIA-PACIFIC 15 \u00b7 OCEANIA 5 \u00b7 AFRICA 5 \u00b7 AMERICAS 4 \u00b7 EUROPE 4 \u00b7 MIDDLE EAST 2 \u00b7 GLOBAL 1",
              1, INK, True, "center")
    draw_text(cv, 512, 110, "Asia-Pacific leads the day \u2014 15 of 36 stories, as the wires reported it.",
              1, INK, False, "center")
    cv.hline(12, 120, 1000, RULE)

    # numbers row
    for i, (num, lab1, lab2) in enumerate(NUMBERS):
        cx = 12 + i * 166 + 83
        draw_text(cv, cx, 128, num, 4, INK, True, "center")
        draw_text(cv, cx, 160, lab1, 1, INK, True, "center")
        draw_text(cv, cx, 169, lab2, 1, INK, True, "center")
        if i:
            cv.vline(12 + i * 166, 126, 50, LIGHT)
    cv.hline(12, 180, 1000, RULE)

    # heroes
    for i, hero in enumerate(HEROES):
        x = 12 + i * 338
        w = 324
        SCENES[hero["scene"]](cv, x, 184, w, 106)
        cv.fill_rect(x, 184, w, 20, NAVY)
        draw_text(cv, x + 8, 186, str(hero["num"]), 2, WHITE, True)
        draw_text(cv, x + 34, 189, hero["region"], 1, WHITE, True)
        y = draw_para(cv, x, 294, hero["head"], w, 2, INK, True, leading=1, max_lines=3)
        y = draw_para(cv, x, y + 3, hero["deck"], w, 1, INK, False, leading=2, max_lines=3)
        draw_text(cv, x, y + 3, hero["src"], 1, INK, True)
        bx = x + text_w(hero["src"], 1, True) + 8
        draw_text(cv, bx, y + 3, hero["badge"], 1, BADGE_COLOR[hero["badge"]], True)
    cv.hline(12, 386, 1000, RULE)

    # section header
    draw_text(cv, 12, 390, "THE DAY IN ELEVEN", 2, INK, True)
    draw_text(cv, 1012, 393, "EVERY PICTURE DRAWN IN CODE \u00b7 EVERY STORY SOURCED", 1, INK, False, "right")
    cv.hline(12, 406, 1000, RULE)

    # cards
    for idx, card in enumerate(CARDS):
        row, col = divmod(idx, 4)
        x = 12 + col * 253
        y = 410 + row * 124
        w = 241
        SCENES[card["scene"]](cv, x, y, w, 42)
        cv.fill_rect(x, y + 28, w, 14, NAVY)
        draw_text(cv, x + 6, y + 31, str(card["num"]), 1, WHITE, True)
        draw_text(cv, x + 30, y + 31, card["region"], 1, WHITE, True)
        y2 = draw_para(cv, x, y + 46, card["head"], w, 2, INK, True, leading=1, max_lines=3)
        y2 = draw_para(cv, x, y2 + 2, card["deck"], w, 1, INK, False, leading=2, max_lines=2)
        draw_text(cv, x, y + 113, card["src"], 1, INK, True)
        bx = x + text_w(card["src"], 1, True) + 8
        draw_text(cv, bx, y + 113, card["badge"], 1, BADGE_COLOR[card["badge"]], True)
    # how-sure legend in the empty 12th slot
    lx, ly = 12 + 3 * 253, 410 + 2 * 124
    cv.rect(lx, ly, 241, 120, RULE)
    cv.fill_rect(lx, ly, 241, 20, NAVY)
    draw_text(cv, lx + 8, ly + 3, "HOW SURE", 2, WHITE, True)
    for j, (word, color, note) in enumerate((
            ("CONFIRMED", GREEN, "a primary source confirms it"),
            ("OFFICIAL", NAVY2, "announced by an official body"),
            ("REPORTED", RED, "as reported by the outlet"))):
        yy = ly + 28 + j * 30
        cv.fill_rect(lx + 8, yy + 1, 10, 10, color)
        draw_text(cv, lx + 24, yy, word, 1, INK, True)
        draw_text(cv, lx + 24, yy + 11, note, 1, INK, False)

    # map + briefs header
    draw_text(cv, 12, 784, "WHERE IT HAPPENED", 2, INK, True)
    draw_text(cv, 12 + text_w("WHERE IT HAPPENED", 2, True) + 10, 787,
              "\u2014 pins carry story numbers", 1, INK, False)
    draw_text(cv, 1012, 784, "ALSO ON WEDNESDAY \u2014 22 MORE STORIES", 2, INK, True, "right")
    cv.hline(12, 802, 1000, RULE)

    # map + briefs
    draw_map(cv, 12, 806, 290, 114, PINS)
    draw_text(cv, 12, 922, "Pin 3: Tokyo \u00b7 Seoul \u00b7 Taipei", 1, INK, False)
    for i, (num, text) in enumerate(BRIEFS):
        col = 0 if i < 11 else 1
        bx = 314 + col * 352
        by = 806 + (i % 11) * 10
        draw_text(cv, bx, by, str(num), 1, RED, True)
        draw_text(cv, bx + 16, by, text, 1, INK, False)

    # date check
    cv.fill_rect(12, 930, 1000, 62, REDBG)
    cv.rect(12, 930, 1000, 62, RED, t=2)
    draw_text(cv, 22, 936, "DATE CHECK", 2, RED, True)
    draw_para(cv, 22, 952,
              "Left out as other days' news \u2014 Tue 24 Nov: Huawei verdict, Chen probe announced, "
              "first PIF tower strike, Nvidia -5.9%, Markle charges, Senegal AFCON restored, Sarkozy "
              "ordered to trial, Sweden vote announced, Nepal quake, O'Hare radar fault, Real Madrid 5-1. "
              "Mon 23 Nov: Huang's return, Mediazona 500,000 war dead, UK Myanmar sanctions. "
              "Sun 22 Nov: COP31 fails. Sat 21 Nov: Sparta II drone strike.",
              980, 1, INK, False, leading=2)

    # footer
    draw_text(cv, 512, 996,
              "Sources: Reuters, AP, AFP, ABS, pm.gov.au, Yonhap, QNA, SCMP, Cybernews, SeatBeat, LiveLaw, AJP.",
              1, INK, False, "center")
    draw_text(cv, 512, 1005,
              "Every story happened or was first reported on Wednesday 25 November 2026, as the named outlets reported it.",
              1, INK, False, "center")
    draw_text(cv, 512, 1014,
              "Asia-Pacific leads the day \u2014 15 of 36 stories. Drawn by an AI agent for make.fun \u2014 one page, one day.",
              1, INK, False, "center")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    data = png_bytes(cv.px, W, H)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
