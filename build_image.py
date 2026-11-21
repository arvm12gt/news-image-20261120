#!/usr/bin/env python3
"""Paint the 20 November 2026 front page: THE WORLD IN ONE IMAGE.

One 1024x1024 PNG, drawn entirely by this script with Pillow -- no
generated pictures, no network, no fonts beyond the DejaVu faces that
ship with the system. The page carries 42 sourced stories from Friday
20 November 2026: the Russian barrage of Kyiv's bridges spilling into
Poland leads, four panels cover the Gulf blockade, the AI selloff,
the COP31 deadlock and Trump's return from Shenzhen, and a three-column
wire ("THE DAY IN BRIEF") holds the other 37. A date-check box stamps
the day on the masthead so the picture can never be mistaken for
another day's news.

Run it with:  python3 build_image.py
It writes entry.png next to this file and a copy to /output/entry.png.
The output is deterministic: run it twice, the bytes match.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

SIDE = 1024
MARGIN = 44
SPAN = SIDE - 2 * MARGIN          # 936, the width of the live area

# The palette: newsprint cream, near-black ink, and four signal colours.
CREAM = (247, 242, 231)
INK = (25, 25, 34)
SIGNAL_RED = (179, 49, 42)
DEEP_BLUE = (20, 64, 107)
BRASS = (201, 162, 39)
HAZE = (150, 144, 128)
SNOW = (255, 255, 255)
PINE = (31, 110, 96)

FONT_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
)


class Type:
    """Font lookup with a small cache; measures with the font itself."""

    def __init__(self):
        self._fonts = {}
        self._paths = {}

    def _locate(self, heavy):
        if heavy in self._paths:
            return self._paths[heavy]
        wanted = "DejaVuSans-Bold.ttf" if heavy else "DejaVuSans.ttf"
        for folder in FONT_DIRS:
            candidate = os.path.join(folder, wanted)
            if os.path.exists(candidate):
                self._paths[heavy] = candidate
                return candidate
        # Fall back to whatever bold/regular face the system offers.
        for folder in FONT_DIRS:
            for name in sorted(os.listdir(folder)):
                if name.endswith(".ttf") and ("Bold" in name) == heavy:
                    found = os.path.join(folder, name)
                    self._paths[heavy] = found
                    return found
        raise FileNotFoundError(wanted)

    def face(self, heavy, size):
        key = (heavy, size)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(self._locate(heavy), size)
        return self._fonts[key]

    @staticmethod
    def measure(text, face):
        return face.getlength(text)


def wrap_lines(text, face, max_w):
    """Yield word-wrapped lines measured with the real font metrics."""
    words = text.split()
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if face.getlength(trial) <= max_w:
            current = trial
            continue
        if current:
            yield current
        current = word
    if current:
        yield current


def fit_text(ty, text, heavy, top_size, floor_size, max_w, max_h,
             leading=1.18, limit=None):
    """Step the size down until the wrapped text fits the box.

    Returns (face, lines, line_height)."""
    size = top_size
    while True:
        face = ty.face(heavy, size)
        lines = list(wrap_lines(text, face, max_w))
        step = max(1, round(size * leading))
        fits = step * len(lines) <= max_h
        if limit is not None:
            fits = fits and len(lines) <= limit
        if fits or size <= floor_size:
            return face, lines, step
        size -= 1


class Poster:
    """A drawing surface that tracks its own vertical cursor."""

    def __init__(self):
        self.img = Image.new("RGB", (SIDE, SIDE), CREAM)
        self.d = ImageDraw.Draw(self.img)
        self.ty = Type()
        self.checks = []

    def record(self, label, box_h, used_h, lines=None):
        self.checks.append((label, box_h, used_h, lines))

    def text(self, x, y, s, face, colour):
        self.d.text((x, y), s, font=face, fill=colour)

    def block(self, x, y, lines, face, step, colour, centre=None):
        """Draw wrapped lines; centre them inside `centre` when given."""
        for line in lines:
            lx = x
            if centre is not None:
                lx = x + (centre - self.ty.measure(line, face)) / 2
            self.d.text((lx, y), line, font=face, fill=colour)
            y += step
        return y

    def caps(self, x, y, s, face, colour, gap=4):
        """Letterspaced capitals, as newspaper kickers are set."""
        cursor = x
        for ch in s:
            self.d.text((cursor, y), ch, font=face, fill=colour)
            cursor += self.ty.measure(ch, face) + gap
        return cursor - gap

    def rule(self, y, weight=2, colour=INK, x0=None, x1=None):
        self.d.rectangle([x0 or MARGIN, y, x1 or (SIDE - MARGIN),
                          y + weight], fill=colour)

    def save(self):
        os.makedirs("/output", exist_ok=True)
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "entry.png")
        self.img.save("/output/entry.png", format="PNG", optimize=True)
        self.img.save(here, format="PNG", optimize=True)
        n = os.path.getsize("/output/entry.png")
        print(f"saved /output/entry.png: {SIDE}x{SIDE}, {n} bytes")
        print("--- layout measurements (box -> used) ---")
        for label, box_h, used_h, lines in self.checks:
            flag = "OK " if used_h <= box_h else "OVERFLOW"
            print(f"{flag} {label}: box h={box_h} used h={used_h} "
                  f"lines={lines}")


# ------------------------------------------------------------- pictograms ----
# Each one is a small vector vignette for a story: bridges under fire,
# a tanker among mines, a plunging market, a warming globe, three flags.

def draw_kyiv(p, x, y, w, h):
    """Kyiv under barrage: skyline, three river bridges, diving missiles."""
    d = p.d
    base = y + h
    # skyline silhouette behind the bridges
    for i, (fx, fh) in enumerate(((0.03, 0.34), (0.10, 0.52), (0.18, 0.40),
                                  (0.62, 0.44), (0.70, 0.58), (0.79, 0.36),
                                  (0.88, 0.48))):
        bw = w * 0.06
        bx = x + w * fx
        d.rectangle([bx, base - h * fh - 30, bx + bw, base - 30], fill=HAZE)
    # the river: two bands at the foot
    d.rectangle([x, base - 12, x + w, base - 7], fill=PINE)
    d.rectangle([x, base - 5, x + w, base], fill=DEEP_BLUE)
    # three bridge decks; the middle one is broken by a blast
    for i, fx in enumerate((0.16, 0.50, 0.84)):
        cx = x + w * fx
        half = w * 0.115
        d.rectangle([cx - half, base - 32, cx + half, base - 25], fill=INK)
        d.arc([cx - half, base - 46, cx + half, base - 18], 180, 360,
              fill=DEEP_BLUE, width=4)
        if i == 1:
            d.rectangle([cx - 9, base - 32, cx + 9, base - 25], fill=CREAM)
            for j in range(4):
                t = j / 3.0
                px = cx + 7 * t
                py = base - 38 - 15 * t
                r = 4 + 5 * t
                d.ellipse([px - r, py - r, px + r, py + r], fill=HAZE)
    # missiles diving in from the top corners, warheads glowing
    for (sx, ex) in ((0.05, 0.28), (0.95, 0.72)):
        d.line([x + w * sx, y + 2, x + w * ex, y + h * 0.42],
               fill=SIGNAL_RED, width=4)
        d.ellipse([x + w * ex - 5, y + h * 0.42 - 5, x + w * ex + 5,
                   y + h * 0.42 + 5], fill=BRASS, outline=SIGNAL_RED,
                  width=2)
    # blast star over the broken span
    cx, cy = x + w * 0.50, y + h * 0.50
    for outer, inner, colour in ((0.20, 0.09, BRASS), (0.11, 0.05,
                                                       SIGNAL_RED)):
        pts = []
        for i in range(16):
            r = h * (outer if i % 2 == 0 else inner)
            a = -math.pi / 2 + i * math.pi / 8
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=colour)


def draw_tanker(p, x, y, s):
    """A tanker on a mined strait, one hold on fire."""
    d = p.d
    # three wave bands
    for i, frac in enumerate((0.74, 0.83, 0.92)):
        colour = DEEP_BLUE if i % 2 == 0 else PINE
        d.rectangle([x, y + s * frac, x + s, y + s * (frac + 0.05)],
                    fill=colour)
    # hull: a flat-bottomed trapezoid, deck tanks as white drums
    d.polygon([(x + s * 0.06, y + s * 0.63), (x + s * 0.94, y + s * 0.63),
               (x + s * 0.86, y + s * 0.75), (x + s * 0.14, y + s * 0.75)],
              fill=INK)
    for frac in (0.26, 0.46, 0.66):
        cx = x + s * frac
        d.ellipse([cx - 12, y + s * 0.52, cx + 12, y + s * 0.63], fill=SNOW,
                  outline=INK, width=3)
    d.rectangle([x + s * 0.80, y + s * 0.46, x + s * 0.89, y + s * 0.63],
                fill=SIGNAL_RED)
    # fire over the forward hold: a gold star with a red heart
    cx, cy = x + s * 0.22, y + s * 0.32
    for outer, inner, colour in ((0.23, 0.10, BRASS), (0.12, 0.05,
                                                       SIGNAL_RED)):
        pts = []
        for i in range(16):
            r = s * (outer if i % 2 == 0 else inner)
            a = -math.pi / 2 + i * math.pi / 8
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=colour)
    # two spiked mines drifting to starboard
    for fx, fy in ((0.70, 0.87), (0.88, 0.81)):
        mx, my = x + s * fx, y + s * fy
        d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=INK)
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            d.line([mx + 7 * math.cos(a), my + 7 * math.sin(a),
                    mx + 12 * math.cos(a), my + 12 * math.sin(a)],
                   fill=INK, width=2)


def draw_market(p, x, y, s):
    """A market in free fall: shrinking bars, a plunging gold line."""
    d = p.d
    # axes
    d.line([x + 6, y + s * 0.08, x + 6, y + s * 0.88], fill=INK, width=3)
    d.line([x + 6, y + s * 0.88, x + s - 4, y + s * 0.88], fill=INK, width=3)
    # six bars, tall on the left, cut down on the right
    n = 6
    step = (s - 22) / n
    tops = []
    for i in range(n):
        frac = (0.30, 0.38, 0.46, 0.55, 0.66, 0.78)[i]
        bx = x + 10 + i * step
        top = y + s * 0.88 - s * frac * 0.82
        colour = DEEP_BLUE if i < 3 else SIGNAL_RED
        d.rectangle([bx, top, bx + step - 5, y + s * 0.88], fill=colour)
        tops.append((bx + (step - 5) / 2, top - 4))
    # the gold line joins the bar tops, ending in a down arrow
    d.line(tops, fill=BRASS, width=4, joint="curve")
    ex, ey = tops[-1]
    d.polygon([(ex - 8, ey - 2), (ex + 2, ey - 10), (ex + 8, ey + 4)],
              fill=BRASS)


def draw_climate(p, x, y, s):
    """A warming globe beside a smoking chimney."""
    d = p.d
    cx, cy = x + s * 0.40, y + s * 0.58
    r = s * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINE, outline=INK,
              width=3)
    # meridians: two arcs across the disc
    d.arc([cx - r, cy - r, cx + r, cy + r], 90, 270, fill=DEEP_BLUE, width=3)
    d.arc([cx - r * 0.55, cy - r, cx + r * 0.55, cy + r], 90, 270,
          fill=DEEP_BLUE, width=2)
    # land in brass: one blob north-west, one south-east
    d.ellipse([cx - r * 0.60, cy - r * 0.60, cx + r * 0.02, cy - r * 0.08],
              fill=BRASS)
    d.ellipse([cx - r * 0.05, cy + r * 0.08, cx + r * 0.58, cy + r * 0.55],
              fill=BRASS)
    # chimney on the right, smoke curling up and away
    sx = x + s * 0.80
    d.polygon([(sx - 8, y + s * 0.95), (sx + 8, y + s * 0.95),
               (sx + 6, y + s * 0.45), (sx - 6, y + s * 0.45)], fill=INK)
    for i in range(4):
        t = i / 3.0
        px = sx + 8 * t
        py = y + s * (0.40 - 0.10 * t)
        rr = 5 + 6 * t
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=HAZE)
    # a red thermometer tick at the foot
    d.rectangle([x + 4, y + s * 0.86, x + s * 0.30, y + s * 0.92],
                fill=SIGNAL_RED)


def draw_flags(p, x, y, s):
    """Three flags over a summit table: the diplomacy vignette."""
    d = p.d
    base = y + s
    d.rectangle([x, base - 24, x + s, base - 20], fill=BRASS)
    d.rectangle([x, base - 18, x + s, base - 6], fill=INK)
    d.rectangle([x, base - 4, x + s, base], fill=DEEP_BLUE)
    fw, fh = s * 0.26, s * 0.16
    for i, colour in enumerate((SIGNAL_RED, DEEP_BLUE, BRASS)):
        px = x + s * (0.06 + 0.30 * i)
        top = y + 4 + (8 if i == 1 else 0)
        d.line([px, top, px, base - 18], fill=INK, width=5)
        d.polygon([(px, top), (px + fw, top + 4),
                   (px + fw - 8, top + fh / 2), (px + fw, top + fh - 4),
                   (px, top + fh)], fill=colour, outline=INK)
        d.ellipse([px - 4, top - 5, px + 4, top + 3], fill=BRASS)


# ------------------------------------------------------------- wire items ----
# 37 one-line stories for "THE DAY IN BRIEF". Every item is dated
# 20 November 2026 in its source (Standard Topic's world archive,
# Moneycontrol, Morningstar/Dow Jones, TradersView and the wire services
# behind the fincazelda.eu / 4designers.eu aggregations). The tag names
# the outlet or agency that reported it.
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


def wrap_wire(headline, tag, face, tag_face, col_w):
    """Wrap one wire headline; the tag rides on its first line."""
    tag_w = tag_face.getlength(tag) + 8
    lines, current, room = [], "", col_w - tag_w
    for word in headline.split():
        trial = word if not current else current + " " + word
        if face.getlength(trial) <= room:
            current = trial
        else:
            lines.append(current)
            current, room = word, col_w
    if current:
        lines.append(current)
    return lines, tag_w, tag


# ------------------------------------------------------------------ build ----
def build():
    p = Poster()
    d, ty = p.d, p.ty

    # ---- masthead: title, date line, date-check box ----
    face, lines, step = fit_text(ty, "THE WORLD IN ONE IMAGE", True, 52,
                                 40, SPAN, 58, leading=1.0, limit=1)
    p.block(MARGIN, 8, lines, face, step, INK, centre=SPAN)
    p.record("masthead title", 58, step * len(lines), lines)

    p.text(MARGIN, 66, "FRIDAY · 20 NOVEMBER 2026 · 42 STORIES · SOURCED",
           ty.face(False, 20), DEEP_BLUE)

    bx0, bx1 = SIDE - MARGIN - 210, SIDE - MARGIN
    d.rectangle([bx0, 58, bx1, 94], outline=SIGNAL_RED, width=3)
    for txt, size, colour, dy in (("DATE CHECK ✓", 15, SIGNAL_RED, 3),
                                  ("FRI 20 NOV 2026", 13, INK, 19)):
        f = ty.face(True, size)
        p.text((bx0 + bx1 - ty.measure(txt, f)) / 2, 58 + dy, txt, f,
               colour)
    p.record("date-check box", 36, 36, ["DATE CHECK ✓", "FRI 20 NOV 2026"])

    p.rule(102, weight=5)
    p.rule(111, weight=2)

    # ---- lead: kicker, vignette, headline, deck ----
    y = 118
    p.caps(MARGIN, y, "UKRAINE", ty.face(True, 14), SIGNAL_RED)
    draw_kyiv(p, MARGIN, y + 20, SPAN, 56)
    y += 20 + 56 + 6
    face, lines, step = fit_text(
        ty, "RUSSIA'S BIGGEST BARRAGE HITS KYIV BRIDGES — AND SPILLS INTO "
            "POLAND", True, 34, 28, SPAN, 76, leading=1.12, limit=2)
    p.block(MARGIN, y, lines, face, step, INK)
    p.record("lead headline", 76, step * len(lines), lines)
    y += step * len(lines) + 6
    face, lines, step = fit_text(
        ty, "More than 400 drones and 110 missiles rain on Ukraine; three "
            "bridges over the Dnipro are struck, eight people are killed — "
            "and two Russian missiles land in NATO member Poland.",
        False, 18, 16, SPAN, 324 - y, leading=1.28, limit=2)
    p.block(MARGIN, y, lines, face, step, INK)
    p.record("lead caption", 324 - y + 6, step * len(lines), lines)

    p.rule(332, weight=2)

    # ---- four panels in a 2x2 grid ----
    grid_top, grid_bot = 340, 556
    row_h = (grid_bot - grid_top - 8) // 2
    col_w = (SPAN - 28) // 2
    d.line([SIDE // 2, grid_top + 4, SIDE // 2, grid_bot - 4], fill=INK,
           width=2)
    d.rectangle([MARGIN, grid_top + row_h + 3, SIDE - MARGIN,
                 grid_top + row_h + 5], fill=INK)

    panels = [
        ("GULF", draw_tanker,
         "TANKERS BURN AS U.S. BLOCKADES HORMUZ",
         "Iran threatens Gulf oil facilities; the IEA calls the disruption "
         "the largest energy shock on record."),
        ("MARKETS", draw_market,
         "AI SELLOFF WIPES $4 TRILLION OFF WALL STREET",
         "KOSPI -4.7%, Nikkei -4.8%, Nasdaq faces its worst November "
         "since 2008."),
        ("CLIMATE", draw_climate,
         "COP31 DRAFT DENOUNCED AS FOSSIL TALKS STALL",
         "Activists denounce the Antalya draft as negotiators deadlock over "
         "how to address fossil fuels."),
        ("DIPLOMACY", draw_flags,
         "TRUMP DEFENDS HIS PUTIN AND XI TIES",
         "Back in Washington, Trump hails the Shenzhen summit — analysts say "
         "it produced little progress."),
    ]
    for idx, (kicker, draw, headline, deck) in enumerate(panels):
        px = MARGIN + (idx % 2) * (col_w + 28)
        py = grid_top + (idx // 2) * (row_h + 8)
        p.caps(px, py, kicker, ty.face(True, 12), SIGNAL_RED)
        top = py + 16
        room_h = py + row_h - top
        draw(p, px, top + (room_h - 68) // 2, 68)
        tx, tw = px + 100, col_w - 100
        face, lines, step = fit_text(ty, headline, True, 22, 18, tw,
                                     int(room_h * 0.56), leading=1.14,
                                     limit=2)
        p.block(tx, top, lines, face, step, INK)
        p.record(f"panel {kicker} headline", int(room_h * 0.56),
                 step * len(lines), lines)
        cap_y = top + step * len(lines) + 6
        face, lines, step = fit_text(ty, deck, False, 14, 12, tw,
                                     py + row_h - cap_y, leading=1.22,
                                     limit=2)
        p.block(tx, cap_y, lines, face, step, INK)
        p.record(f"panel {kicker} caption", py + row_h - cap_y,
                 step * len(lines), lines)

    p.rule(564, weight=2)

    # ---- the wire: header, then three balanced columns ----
    p.text(MARGIN, 572, "THE DAY IN BRIEF · 37 MORE STORIES",
           ty.face(True, 16), INK)
    tail = "WIRE · 20 NOV 2026 (UTC)"
    tf = ty.face(False, 13)
    p.text(SIDE - MARGIN - ty.measure(tail, tf), 575, tail, tf, DEEP_BLUE)

    wire_top, wire_bot = 598, 978
    wire_h = wire_bot - wire_top
    wcol_w = (SPAN - 2 * 16) // 3
    wcol_x = [MARGIN + i * (wcol_w + 16) for i in range(3)]
    picked = None
    for size in (14, 13, 12):
        wf, tface = ty.face(False, size), ty.face(True, size)
        wrapped = [wrap_wire(head, tag, wf, tface, wcol_w)
                   for tag, head in WIRE]
        wrapped.sort(key=lambda item: -len(item[0]))
        cols, heights = [[], [], []], [0, 0, 0]
        for item in wrapped:
            ci = heights.index(min(heights))
            cols[ci].append(item)
            heights[ci] += len(item[0])
        if max(heights) * size <= wire_h:
            picked = (size, cols, heights)
            break
    size, cols, heights = picked
    wf, tface = ty.face(False, size), ty.face(True, size)
    p.record("wire columns", wire_h, max(heights) * size,
             [f"size={size} lines={heights}"])
    for ci, items in enumerate(cols):
        cy = wire_top
        for lines, tag_w, tag in items:
            p.text(wcol_x[ci], cy, tag, tface, SIGNAL_RED)
            for li, line in enumerate(lines):
                lx = wcol_x[ci] + (tag_w if li == 0 else 0)
                p.text(lx, cy, line, wf, INK)
                cy += size

    # ---- footer band: three highlights on navy ----
    d.rectangle([0, 986, SIDE, SIDE], fill=DEEP_BLUE)
    face, lines, step = fit_text(
        ty, "ALSO TODAY · GTA VI banks nearly $4B on launch day · "
            "Van Gogh fetches a record $190.4M · Fiona the hippo dies "
            "at her U.S. zoo",
        False, 14, 12, SPAN, 34, leading=1.22, limit=2)
    p.block(MARGIN, 986 + (38 - step * len(lines)) // 2, lines, face, step,
            SNOW)
    p.record("footer", 38, step * len(lines), lines)

    p.save()


if __name__ == "__main__":
    build()
