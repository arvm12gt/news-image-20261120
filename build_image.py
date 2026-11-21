#!/usr/bin/env python3
"""Render entry.png (1024x1024): an editorial front-page poster that sums up
20 November 2026 world news in one image -- a lead story, four panels, and a
dense 37-item sourced wire section (42 stories in total, date-checked).
Everything is drawn in code with Pillow -- crisp vector-style shapes and real
rendered text, so every headline stays legible (unlike AI-generated images).
Run:  python3 build_image.py   ->  writes entry.png here (and /output).
Deterministic: same input always produces byte-identical output.
"""

import glob
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = "/output"
OUT = os.path.join(OUT_DIR, "entry.png")
LOCAL = os.path.join(HERE, "entry.png")

W = H = 1024
PAPER = (247, 242, 231)   # #f7f2e7
INK = (25, 25, 34)        # #191922
RED = (179, 49, 42)       # #b3312a
NAVY = (20, 64, 107)      # #14406b
GOLD = (201, 162, 39)     # #c9a227
SMOKE = (150, 144, 128)
WHITE = (255, 255, 255)
TEAL = (31, 110, 96)      # #1f6e60

MARGIN = 44
CONTENT_W = W - 2 * MARGIN  # 936


# ---------------------------------------------------------------- fonts ----
def find_font(*patterns):
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    raise FileNotFoundError(patterns)


BOLD_PATH = find_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/**/NotoSans-Bold.ttf",
    "/usr/share/fonts/**/LiberationSans-Bold.ttf",
)
REG_PATH = find_font(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/**/NotoSans-Regular.ttf",
    "/usr/share/fonts/**/LiberationSans-Regular.ttf",
)

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def bold(size):
    return font(BOLD_PATH, size)


def regular(size):
    return font(REG_PATH, size)


# ------------------------------------------------------------ text utils ----
_probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def text_w(text, fnt):
    return _probe.textlength(text, font=fnt)


def wrap(text, fnt, max_w):
    """Greedy word wrap measured with the real font metrics."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(text, path, start, minimum, max_w, max_h, lh_factor=1.18,
              max_lines=None):
    """Shrink the font until the wrapped block fits the box.

    Returns (font, lines, line_height, total_height)."""
    size = start
    while size >= minimum:
        fnt = font(path, size)
        lines = wrap(text, fnt, max_w)
        lh = int(size * lh_factor)
        total = lh * len(lines)
        if total <= max_h and (max_lines is None or len(lines) <= max_lines):
            return fnt, lines, lh, total
        size -= 1
    fnt = font(path, minimum)
    lines = wrap(text, fnt, max_w)
    lh = int(minimum * lh_factor)
    return fnt, lines, lh, lh * len(lines)


def draw_lines(d, x, y, lines, fnt, lh, fill, align="left", box_w=None):
    for line in lines:
        if align == "center":
            lx = x + (box_w - text_w(line, fnt)) / 2
        else:
            lx = x
        d.text((lx, y), line, font=fnt, fill=fill)
        y += lh
    return y


def draw_tracked(d, x, y, text, fnt, fill, tracking=3):
    """Draw letterspaced caps (for kickers); returns the end x."""
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=fnt, fill=fill)
        cx += text_w(ch, fnt) + tracking
    return cx - tracking


REPORT = []


def note(name, box, used_h, lines=None):
    REPORT.append((name, box, used_h, lines))


# ------------------------------------------------------------- pictograms ----
def pic_bridges(d, x, y, w, h):
    """Kyiv under barrage: three Dnipro bridges, missile streaks, blasts."""
    base = y + h
    # river band at the bottom
    d.rectangle([x, base - 14, x + w, base - 8], fill=TEAL)
    d.rectangle([x, base - 6, x + w, base], fill=NAVY)
    # three bridge decks with arches, one deck broken in the middle
    for i, fx in enumerate((0.14, 0.50, 0.86)):
        cx = x + w * fx
        bw = w * 0.24
        d.rectangle([cx - bw / 2, base - 34, cx + bw / 2, base - 26],
                    fill=INK)
        d.arc([cx - bw / 2, base - 52, cx + bw / 2, base - 22], start=180,
              end=360, fill=NAVY, width=4)
        if i == 1:
            # broken middle deck: a gap with a smoke plume
            d.rectangle([cx - 8, base - 34, cx + 8, base - 26], fill=PAPER)
            for j in range(4):
                t = j / 3.0
                px = cx + 6 * t
                py = base - 40 - 14 * t
                r = 4 + 5 * t
                d.ellipse([px - r, py - r, px + r, py + r], fill=SMOKE)
    # missile streaks diving from the top corners
    for (sx, sy, ex, ey) in ((0.06, 0.02, 0.30, 0.42),
                             (0.94, 0.02, 0.70, 0.42),
                             (0.52, 0.00, 0.50, 0.30)):
        d.line([x + w * sx, y + h * sy, x + w * ex, y + h * ey], fill=RED,
               width=4)
        d.ellipse([x + w * ex - 5, y + h * ey - 5, x + w * ex + 5,
                   y + h * ey + 5], fill=GOLD, outline=RED, width=2)
    # blast star over the middle bridge
    cx, cy = x + w * 0.50, y + h * 0.52
    star = []
    for i in range(16):
        r = h * (0.20 if i % 2 == 0 else 0.09)
        a = -math.pi / 2 + i * math.pi / 8
        star.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star, fill=GOLD)
    star2 = []
    for i in range(12):
        r = h * (0.11 if i % 2 == 0 else 0.05)
        a = -math.pi / 2 + i * math.pi / 6
        star2.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star2, fill=RED)


def pic_tanker(d, x, y, s):
    """Oil tanker on waves with a burst of flame and mine dots."""
    for i, yy in enumerate((0.72, 0.82, 0.92)):
        col = NAVY if i % 2 == 0 else TEAL
        d.rectangle([x, y + s * yy, x + s, y + s * (yy + 0.06)], fill=col)
    d.polygon([(x + s * 0.08, y + s * 0.62), (x + s * 0.92, y + s * 0.62),
               (x + s * 0.84, y + s * 0.74), (x + s * 0.16, y + s * 0.74)],
              fill=INK)
    for f in (0.24, 0.44, 0.64):
        cx = x + s * f
        d.ellipse([cx - 13, y + s * 0.50, cx + 13, y + s * 0.62], fill=WHITE,
                  outline=INK, width=3)
    d.rectangle([x + s * 0.78, y + s * 0.44, x + s * 0.88, y + s * 0.62],
                fill=RED)
    cx, cy = x + s * 0.20, y + s * 0.30
    star = []
    for i in range(16):
        r = s * (0.24 if i % 2 == 0 else 0.11)
        a = -math.pi / 2 + i * math.pi / 8
        star.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star, fill=GOLD)
    star2 = []
    for i in range(12):
        r = s * (0.13 if i % 2 == 0 else 0.06)
        a = -math.pi / 2 + i * math.pi / 6
        star2.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(star2, fill=RED)
    for fx, fy in ((0.68, 0.86), (0.86, 0.80)):
        mx, my = x + s * fx, y + s * fy
        d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=INK)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            d.line([mx + 7 * math.cos(a), my + 7 * math.sin(a),
                    mx + 12 * math.cos(a), my + 12 * math.sin(a)],
                   fill=INK, width=2)


def pic_chart(d, x, y, s):
    """Falling market chart: descending bars and a plunging red line."""
    # axis
    d.line([x + 6, y + s * 0.10, x + 6, y + s * 0.88], fill=INK, width=3)
    d.line([x + 6, y + s * 0.88, x + s - 4, y + s * 0.88], fill=INK, width=3)
    # descending bars, navy to red
    n = 6
    bw = (s - 22) / n
    heights = (0.30, 0.38, 0.46, 0.55, 0.66, 0.78)
    for i, hf in enumerate(heights):
        bx = x + 10 + i * bw
        top = y + s * 0.88 - s * hf * 0.82
        col = NAVY if i < 3 else RED
        d.rectangle([bx, top, bx + bw - 5, y + s * 0.88], fill=col)
    # plunging line across the bar tops
    pts = []
    for i, hf in enumerate(heights):
        px = x + 10 + i * bw + (bw - 5) / 2
        py = y + s * 0.88 - s * hf * 0.82 - 4
        pts.append((px, py))
    d.line(pts, fill=GOLD, width=4, joint="curve")
    # arrowhead at the end, pointing down
    ex, ey = pts[-1]
    d.polygon([(ex - 8, ey - 2), (ex + 2, ey - 10), (ex + 8, ey + 4)],
              fill=GOLD)


def pic_climate(d, x, y, s):
    """A warming globe under a factory smokestack plume."""
    cx, cy = x + s * 0.42, y + s * 0.58
    r = s * 0.30
    # globe
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAL, outline=INK,
              width=3)
    d.arc([cx - r, cy - r, cx + r, cy + r], start=90, end=270, fill=NAVY,
          width=3)
    # landmass blobs
    d.ellipse([cx - r * 0.55, cy - r * 0.55, cx + r * 0.05, cy - r * 0.05],
              fill=GOLD)
    d.ellipse([cx - r * 0.05, cy + r * 0.10, cx + r * 0.55, cy + r * 0.55],
              fill=GOLD)
    # smokestack on the right, smoke curling up
    sx = x + s * 0.78
    d.polygon([(sx - 8, y + s * 0.95), (sx + 8, y + s * 0.95),
               (sx + 6, y + s * 0.45), (sx - 6, y + s * 0.45)], fill=INK)
    for i in range(4):
        t = i / 3.0
        px = sx + 8 * t
        py = y + s * (0.40 - 0.10 * t)
        rr = 5 + 6 * t
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=SMOKE)
    # thermometer sliver at the bottom left
    d.rectangle([x + 4, y + s * 0.86, x + s * 0.30, y + s * 0.92], fill=RED)


def pic_flags(d, x, y, s):
    """Three flag poles over a summit table band (diplomacy).

    All geometry is relative to s so the flags stay inside the box
    at panel size (68px) as well as at full width."""
    base = y + s
    d.rectangle([x, base - 24, x + s, base - 20], fill=GOLD)
    d.rectangle([x, base - 18, x + s, base - 6], fill=INK)
    d.rectangle([x, base - 4, x + s, base], fill=NAVY)
    fw, fh = s * 0.26, s * 0.16
    for i, col in enumerate((RED, NAVY, GOLD)):
        px = x + s * (0.06 + 0.30 * i)
        top = y + 4 + (8 if i == 1 else 0)
        d.line([px, top, px, base - 18], fill=INK, width=5)
        d.polygon([(px, top), (px + fw, top + 4), (px + fw - 8, top + fh / 2),
                   (px + fw, top + fh - 4), (px, top + fh)], fill=col,
                  outline=INK)
        d.ellipse([px - 4, top - 5, px + 4, top + 3], fill=GOLD)


# ------------------------------------------------------------- wire items ----
# 37 one-line stories for "THE DAY IN BRIEF": every item is dated
# 20 November 2026 in its source (Standard Topic world archive, Moneycontrol,
# Morningstar/Dow Jones, TradersView, fincazelda.eu / 4designers.eu wires).
# Tags are the reporting outlet or agency behind each item.
WIRE = [
    ("IEA", "HORMUZ DISRUPTION LARGEST ENERGY SHOCK ON RECORD"),
    ("REUTERS", "OIL PRICES SWING AS TANKER ATTACKS ROIL SUPPLY OUTLOOK"),
    ("AP", "TRUMP FLOATS PENALTIES FOR U.S. FIRMS BUILDING AI CENTRES ABROAD"),
    ("BLOOMBERG", "U.S., CHINA AGREE HUMANS MUST OVERSEE MILITARY AI DECISIONS"),
    ("WSJ", "TRUMP KEEPS CHINA LIMITED TO OLDER AI CHIPS, INCLUDING H200"),
    ("BLOOMBERG", "CHINA BARS BLOOMBERG REPORTER FROM SUMMIT OVER HUANG QUESTION"),
    ("AP", "U.S. EMBASSY: CHINESE CHEMICALS FUEL SINALOA CARTEL"),
    ("REUTERS", "RUSSIA VOWS RETALIATION OVER CRIMEAN BRIDGE SPAN DOWN"),
    ("KYIV POST", "UKRAINE LIBERATES 14 SETTLEMENTS IN KHARKIV OFFENSIVE"),
    ("CNA", "ZELENSKYY IN BERLIN AS EUROPE OFFERS BINDING GUARANTEES"),
    ("AP", "POLAND CONFIRMS TWO RUSSIAN MISSILES FELL IN LUBLIN"),
    ("NDTV", "TOXIC LIQUOR IN MANIPUR KILLS 11, SICKENS MORE THAN 180"),
    ("REUTERS", "YOUNG EUROPEANS PROTEST LIVING COSTS, MILITARY SPENDING"),
    ("JAPAN TIMES", "93% OF JAPANESE SEE TIES WITH CHINA AS POOR, POLL FINDS"),
    ("NDTV", "PAKISTANI MINISTER IN NEW DELHI, FIRST SINCE 2025 CONFLICT"),
    ("NDTV", "BANGLADESH'S BANNED AWAMI LEAGUE CALLS NATIONWIDE PROTEST"),
    ("REUTERS", "ALIBABA DEPLOYS OWN CHIPS AS U.S. TIGHTENS EXPORT CURBS"),
    ("NDTV", "NEPAL PM BALENDRA SHAH HEADS TO INDIA ON SUNDAY"),
    ("CNA", "ALBANESE AND XI HOLD TALKS IN SHENZHEN"),
    ("NDTV", "MODI URGES INDIAN INDUSTRY TO CUT IMPORTS, BOOST OUTPUT"),
    ("AP", "U.S. COMMISSION WARNS CHINA COULD CONTROL DRUG SUPPLY"),
    ("AP", "INDIAN MAN GETS 19+ YEARS FOR NEW YORK MURDER PLOT"),
    ("DOW JONES", "GTA VI HITS NEARLY $4 BILLION IN SALES ON LAUNCH DAY"),
    ("AP", "VAN GOGH PAINTING FETCHES RECORD $190.4 MILLION"),
    ("AP", "FIONA THE HIPPO DIES AT U.S. ZOO AFTER SWALLOWING HAT"),
    ("RNZ", "N.Z. COURT: PAY EQUITY REFORM VIOLATED WOMEN'S RIGHTS"),
    ("AP", "HAITI PASTOR CONVICTED OVER PRESIDENT'S KILLING"),
    ("AP", "34 ALLEGED GANG MEMBERS KILLED IN HAITI POLICE OPERATION"),
    ("AP", "U.S. CHARGES RUSSIAN OVER SPYING ON PALANTIR STAFF"),
    ("AP", "TRUMP ANNOUNCES $22 BILLION OF SOUTHEAST ASIA DEALS"),
    ("REUTERS", "L'OREAL TO BUY 10% STAKE IN ARMANI"),
    ("AP", "22,000+ PALESTINIAN CHILDREN DIED IN GAZA, MINISTRY SAYS"),
    ("AP", "IAEA: NORTH KOREA EXPANDS YONGBYON ENRICHMENT"),
    ("JAPAN TIMES", "SOUTH KOREA COURT ORDERS RETRIAL OF EX-PM HAN"),
    ("AP", "SETTLERS TORCH MOSQUE; ARAB OFFICIALS BLAME NETANYAHU"),
    ("AP", "U.N. RIGHTS CHIEF RAISES CONCERNS OVER IMRAN KHAN"),
    ("DOW JONES", "DATABRICKS IN TALKS TO RAISE FUNDS AT $225 BILLION"),
    ("MONEYCONTROL", "BITCOIN DROPS BELOW $60,000, JPMORGAN SAYS"),
]


def wire_wrap(headline, tag, fnt, col_w, tag_fnt=None):
    """Wrap a wire headline with a red tag prefix on the first line.

    Headline is set in fnt (regular), the tag in tag_fnt (bold).
    Returns (lines, tag_width, tag)."""
    tag_w = text_w(tag, tag_fnt or fnt) + 8
    lines, cur, avail = [], "", col_w - tag_w
    for word in headline.split():
        trial = word if not cur else cur + " " + word
        if text_w(trial, fnt) <= avail:
            cur = trial
        else:
            lines.append(cur)
            cur, avail = word, col_w
    if cur:
        lines.append(cur)
    return lines, tag_w, tag


# ----------------------------------------------------------------- layout ----
def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    f_title, t_lines, t_lh, t_h = fit_block(
        "THE WORLD IN ONE IMAGE", BOLD_PATH, 52, 40, CONTENT_W, 58,
        lh_factor=1.0, max_lines=1)
    draw_lines(d, MARGIN, 8, t_lines, f_title, t_lh, INK,
               align="center", box_w=CONTENT_W)
    note("masthead title", (MARGIN, 8, CONTENT_W, 58), t_h, t_lines)

    date_f = regular(20)
    date_txt = "FRIDAY · 20 NOVEMBER 2026 · 42 STORIES · SOURCED"
    d.text((MARGIN, 66), date_txt, font=date_f, fill=NAVY)

    # date-check corner box (right of the date line)
    bx0, by0, bx1, by1 = W - MARGIN - 210, 58, W - MARGIN, 94
    d.rectangle([bx0, by0, bx1, by1], outline=RED, width=3)
    dc1, dc2 = bold(15), bold(13)
    t1, t2 = "DATE CHECK ✓", "FRI 20 NOV 2026"
    d.text(((bx0 + bx1 - text_w(t1, dc1)) / 2, by0 + 3), t1, font=dc1,
           fill=RED)
    d.text(((bx0 + bx1 - text_w(t2, dc2)) / 2, by0 + 19), t2, font=dc2,
           fill=INK)
    note("date-check box", (bx0, by0, 210, 36), 36, [t1, t2])

    # thin double rules
    d.rectangle([MARGIN, 102, W - MARGIN, 107], fill=INK)
    d.rectangle([MARGIN, 111, W - MARGIN, 113], fill=INK)

    # ---- lead panel (118..324) ----
    lead_top, lead_bot = 118, 324
    draw_tracked(d, MARGIN, lead_top, "UKRAINE", bold(14), RED, tracking=4)
    pic_bridges(d, MARGIN, lead_top + 20, CONTENT_W, 56)
    hy = lead_top + 20 + 56 + 6
    f_h, h_lines, h_lh, h_h = fit_block(
        "RUSSIA'S BIGGEST BARRAGE HITS KYIV BRIDGES — AND SPILLS INTO POLAND",
        BOLD_PATH, 34, 28, CONTENT_W, 76, lh_factor=1.12, max_lines=2)
    draw_lines(d, MARGIN, hy, h_lines, f_h, h_lh, INK)
    note("lead headline", (MARGIN, hy, CONTENT_W, 76), h_h, h_lines)
    cy = hy + h_h + 6
    f_c, c_lines, c_lh, c_h = fit_block(
        "More than 400 drones and 110 missiles rain on Ukraine; three "
        "bridges over the Dnipro are struck, eight people are killed — and "
        "two Russian missiles land in NATO member Poland.",
        REG_PATH, 18, 16, CONTENT_W, lead_bot - cy, lh_factor=1.28,
        max_lines=2)
    draw_lines(d, MARGIN, cy, c_lines, f_c, c_lh, INK)
    note("lead caption", (MARGIN, cy, CONTENT_W, lead_bot - cy), c_h, c_lines)

    # rule under lead
    d.rectangle([MARGIN, 332, W - MARGIN, 334], fill=INK)

    # ---- 2x2 grid (340..556) ----
    grid_top, grid_bot = 340, 556
    row_h = (grid_bot - grid_top - 8) // 2  # 104, gap 8 with rule
    col_w = (CONTENT_W - 28) // 2            # 454, gutter 28
    col_x = [MARGIN, MARGIN + col_w + 28]
    row_y = [grid_top, grid_top + row_h + 8]
    # vertical rule between columns
    d.line([W // 2, grid_top + 4, W // 2, grid_bot - 4], fill=INK, width=2)
    # horizontal rule between rows
    d.rectangle([MARGIN, grid_top + row_h + 3, W - MARGIN,
                 grid_top + row_h + 5], fill=INK)

    panels = [
        ("GULF", pic_tanker,
         "TANKERS BURN AS U.S. BLOCKADES HORMUZ",
         "Iran threatens Gulf oil facilities; the IEA calls the disruption "
         "the largest energy shock on record."),
        ("MARKETS", pic_chart,
         "AI SELLOFF WIPES $4 TRILLION OFF WALL STREET",
         "KOSPI -4.7%, Nikkei -4.8%, Nasdaq faces its worst November "
         "since 2008."),
        ("CLIMATE", pic_climate,
         "COP31 DRAFT DENOUNCED AS FOSSIL TALKS STALL",
         "Activists denounce the Antalya draft as negotiators deadlock over "
         "how to address fossil fuels."),
        ("DIPLOMACY", pic_flags,
         "TRUMP DEFENDS HIS PUTIN AND XI TIES",
         "Back in Washington, Trump hails the Shenzhen summit — analysts say "
         "it produced little progress."),
    ]

    for idx, (kicker, pic, headline, caption) in enumerate(panels):
        px = col_x[idx % 2]
        py = row_y[idx // 2]
        draw_tracked(d, px, py, kicker, bold(12), RED, tracking=4)
        content_top = py + 16
        avail_h = (py + row_h) - content_top
        # pictogram on the left, text on the right
        pic(d, px, content_top + (avail_h - 68) // 2, 68)
        tx = px + 100
        tw = col_w - 100
        # headline gets up to ~55% of the height, caption the rest
        f_h, h_lines, h_lh, h_h = fit_block(
            headline, BOLD_PATH, 22, 18, tw, int(avail_h * 0.56),
            lh_factor=1.14, max_lines=2)
        draw_lines(d, tx, content_top, h_lines, f_h, h_lh, INK)
        note(f"panel {kicker} headline", (tx, content_top, tw,
             int(avail_h * 0.56)), h_h, h_lines)
        cap_y = content_top + h_h + 6
        f_c, c_lines, c_lh, c_h = fit_block(
            caption, REG_PATH, 14, 12, tw, (py + row_h) - cap_y,
            lh_factor=1.22, max_lines=2)
        draw_lines(d, tx, cap_y, c_lines, f_c, c_lh, INK)
        note(f"panel {kicker} caption", (tx, cap_y, tw, (py + row_h) - cap_y),
             c_h, c_lines)

    # rule under grid
    d.rectangle([MARGIN, 564, W - MARGIN, 566], fill=INK)

    # ---- wire section header (572..594) ----
    wh_f = bold(16)
    wh_txt = "THE DAY IN BRIEF · 37 MORE STORIES"
    d.text((MARGIN, 572), wh_txt, font=wh_f, fill=INK)
    wr_f = regular(13)
    wr_txt = "WIRE · 20 NOV 2026 (UTC)"
    d.text((W - MARGIN - text_w(wr_txt, wr_f), 575), wr_txt, font=wr_f,
           fill=NAVY)

    # ---- wire columns (598..978) ----
    wire_top, wire_bot = 598, 978
    wire_h = wire_bot - wire_top
    wcol_w = (CONTENT_W - 2 * 16) // 3  # 301
    wcol_x = [MARGIN, MARGIN + wcol_w + 16, MARGIN + 2 * (wcol_w + 16)]
    # pick the largest wire size whose tallest balanced column fits
    chosen = None
    for size in (14, 13, 12):
        wf = regular(size)
        tf = bold(size)
        lh = size  # caps-only wire text: tight leading, no descenders
        wrapped = [wire_wrap(head, tag, wf, wcol_w, tf)
                   for tag, head in WIRE]
        # longest-first balancing keeps the tallest column minimal
        wrapped.sort(key=lambda it: -len(it[0]))
        cols, heights = [[], [], []], [0, 0, 0]
        for item in wrapped:
            ci = heights.index(min(heights))
            cols[ci].append(item)
            heights[ci] += len(item[0])
        if max(heights) * lh <= wire_h:
            chosen = (size, lh, cols, heights)
            break
    size, lh, cols, heights = chosen
    wf = regular(size)
    tf = bold(size)
    note("wire columns", (MARGIN, wire_top, CONTENT_W, wire_h),
         max(heights) * lh, [f"size={size} lines={heights}"])
    for ci, items in enumerate(cols):
        cy = wire_top
        for lines, tag_w, tag in items:
            d.text((wcol_x[ci], cy), tag, font=tf, fill=RED)
            for li, line in enumerate(lines):
                lx = wcol_x[ci] + (tag_w if li == 0 else 0)
                d.text((lx, cy), line, font=wf, fill=INK)
                cy += lh

    # ---- footer band (986..1024) ----
    d.rectangle([0, 986, W, H], fill=NAVY)
    footer = ("ALSO TODAY · GTA VI banks nearly $4B on launch day · "
              "Van Gogh fetches a record $190.4M · Fiona the hippo dies "
              "at her U.S. zoo")
    f_f, f_lines, f_lh, f_h = fit_block(
        footer, REG_PATH, 14, 12, CONTENT_W, 34, lh_factor=1.22, max_lines=2)
    fy = 986 + (38 - f_h) // 2
    draw_lines(d, MARGIN, fy, f_lines, f_f, f_lh, WHITE)
    note("footer", (MARGIN, 986, CONTENT_W, 38), f_h, f_lines)

    os.makedirs(OUT_DIR, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    img.save(LOCAL, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"saved {OUT}: {img.size[0]}x{img.size[1]}, {size} bytes")
    print("--- layout measurements (box -> used) ---")
    for name, (bx, by, bw, bh), used, lines in REPORT:
        flag = "OK " if used <= bh else "OVERFLOW"
        print(f"{flag} {name}: box h={bh} used h={used} lines={lines}")


if __name__ == "__main__":
    main()
