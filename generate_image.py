#!/usr/bin/env python3
"""Draw entry.png: a newspaper front page summing up the world news of
Saturday 21 November 2026.

Every word is drawn in code with Pillow (DejaVu fonts), so the text
renders exactly as written -- no generated imagery, no photographs,
no garbled text. Each story was checked in at least two outlets on
21 November 2026; SOURCES.md lists the reporting behind each one.
Where an event itself falls on 20 November but was first widely
reported on 21 November, SOURCES.md says so.

Running this script writes entry.png (1024x1024) next to it, and
re-running it reproduces the same bytes. If any panel's text would
overflow its box, the script prints a warning naming the panel, so
an overflow can never slip through silently.
"""

import math

from PIL import Image, ImageDraw, ImageFont

W = 1024
H = 1024
MARGIN = 28

PAPER = (248, 244, 235)
INK = (16, 16, 20)
BODY = (44, 44, 48)
GOLD = (214, 178, 58)
WHITE = (255, 255, 255)
RED = (176, 32, 32)
NAVY = (30, 56, 94)
GREEN = (28, 82, 52)
TEAL = (14, 88, 84)
SLATE = (68, 68, 80)
PURPLE = (84, 48, 110)

FONTS = "/usr/share/fonts/truetype/dejavu"
SERIF = f"{FONTS}/DejaVuSerif-Bold.ttf"
SANS = f"{FONTS}/DejaVuSans.ttf"
SANS_B = f"{FONTS}/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, fnt, width):
    """Greedy word wrap: every returned line fits within `width` px."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_icon(d, kind, cx, cy, colour):
    """A small pictorial glyph, drawn with primitives, inside a 24px
    box centred at (cx, cy) so it always fits the kicker bar."""
    if kind == "blast":  # starburst over a skyline
        for k in range(8):
            a = math.pi * k / 4
            d.line([(cx + 6 * math.cos(a), cy - 5 + 6 * math.sin(a)),
                    (cx + 11 * math.cos(a), cy - 5 + 11 * math.sin(a))],
                   fill=colour, width=2)
        d.ellipse([cx - 4, cy - 9, cx + 4, cy - 1], fill=colour)
        d.rectangle([cx - 12, cy + 3, cx - 6, cy + 11], fill=colour)
        d.rectangle([cx - 4, cy + 0, cx + 2, cy + 11], fill=colour)
        d.rectangle([cx + 4, cy + 5, cx + 12, cy + 11], fill=colour)
    elif kind == "scales":  # scales of justice
        d.line([(cx, cy - 11), (cx, cy + 11)], fill=colour, width=2)
        d.line([(cx - 11, cy - 8), (cx + 11, cy - 8)], fill=colour, width=2)
        d.polygon([(cx - 12, cy + 2), (cx - 5, cy + 2), (cx - 8, cy + 9)],
                  fill=colour)
        d.polygon([(cx + 5, cy + 2), (cx + 12, cy + 2), (cx + 8, cy + 9)],
                  fill=colour)
        d.line([(cx - 11, cy - 8), (cx - 8, cy + 2)], fill=colour, width=1)
        d.line([(cx + 11, cy - 8), (cx + 8, cy + 2)], fill=colour, width=1)
        d.rectangle([cx - 6, cy + 11, cx + 6, cy + 13], fill=colour)
    elif kind == "chart":  # a falling line chart
        d.line([(cx - 13, cy - 7), (cx - 4, cy - 1),
                (cx + 3, cy - 4), (cx + 13, cy + 8)], fill=colour, width=3)
        d.polygon([(cx + 13, cy + 8), (cx + 6, cy + 8), (cx + 13, cy + 1)],
                  fill=colour)
    elif kind == "leaf":  # a leaf in a circle
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], outline=colour, width=2)
        d.ellipse([cx - 6, cy - 3, cx + 6, cy + 8], fill=colour)
        d.line([(cx - 6, cy + 8), (cx + 8, cy - 7)], fill=colour, width=2)
    elif kind == "lock":  # a padlock
        d.arc([cx - 7, cy - 11, cx + 7, cy + 1], start=180, end=0,
              fill=colour, width=3)
        d.rectangle([cx - 10, cy - 1, cx + 10, cy + 11], fill=colour)
        d.ellipse([cx - 2, cy + 2, cx + 2, cy + 6], fill=INK)
    elif kind == "stars":  # a ring of stars
        for k in range(8):
            a = math.pi * k / 4
            x = cx + 10 * math.cos(a)
            y = cy + 10 * math.sin(a)
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=colour)


def render_panel(d, spec):
    """One news panel: coloured kicker bar with a glyph, serif headline,
    body text. Warns (and returns False) if the text would overflow."""
    x0, y0, x1, y1 = spec["box"]
    colour = spec["colour"]
    d.rectangle([x0, y0, x1, y0 + 34], fill=colour)
    d.text((x0 + 12, y0 + 6), spec["kicker"],
           font=font(SANS_B, 20), fill=WHITE)
    draw_icon(d, spec["icon"], x1 - 26, y0 + 17, WHITE)
    y = y0 + 46
    head = font(SERIF, spec["head_size"])
    head_lines = wrap(d, spec["headline"], head, (x1 - x0) - 24)
    for line in head_lines:
        d.text((x0 + 12, y), line, font=head, fill=INK)
        y += spec["head_size"] + 7
    y += 3
    body = font(SANS, spec["body_size"])
    body_lines = wrap(d, spec["body"], body, (x1 - x0) - 24)
    fits = True
    for line in body_lines:
        if y + spec["body_size"] > y1 - 4:
            fits = False
            break
        d.text((x0 + 12, y), line, font=body, fill=BODY)
        y += spec["body_size"] + 6
    if not fits:
        print(f"WARNING overflow in panel {spec['kicker']!r}: "
              f"{len(body_lines)} body lines do not fit")
    print(f"panel {spec['kicker']!r}: headline {len(head_lines)} lines, "
          f"body {len(body_lines)} lines, fits={fits}")
    return fits


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    right = W - MARGIN
    ok = True

    # ---------- masthead ----------
    d.rectangle([0, 0, W, 148], fill=INK)
    d.text((W / 2, 12), "THE WORLD IN ONE IMAGE",
           font=font(SANS_B, 24), fill=GOLD, anchor="ma")
    d.text((W / 2, 44), "SATURDAY", font=font(SERIF, 36), fill=WHITE, anchor="ma")
    d.text((W / 2, 86), "21 NOVEMBER 2026",
           font=font(SERIF, 52), fill=WHITE, anchor="ma")
    d.rectangle([0, 148, W, 154], fill=RED)

    # ---------- lead story: Russia strikes Ukraine again; missiles in Poland ----------
    ok &= render_panel(d, {
        "box": (MARGIN, 164, right, 358),
        "kicker": "KYIV \u00b7 WARSAW",
        "colour": RED,
        "icon": "blast",
        "headline": "KYIV HIT AGAIN; MISSILES LAND IN POLAND",
        "head_size": 34,
        "body": "Russia fired 3 ballistic missiles and 148 drones at "
                "Ukraine overnight; air defences downed 117 of the "
                "drones. A morning strike on Kyiv injured 2, damaged "
                "homes in 3 districts and cut water in 5. In Kryvyi "
                "Rih, 2 were killed and 58 wounded. Two Russian "
                "missiles and a suspected drone fell in Poland; PM "
                "Tusk called it a deliberate provocation.",
        "body_size": 19,
    })

    # ---------- four panels in a grid ----------
    mid = W // 2
    left = (MARGIN, mid - 13)
    right_col = (mid + 13, right)
    top_row = (370, 556)
    bot_row = (568, 754)

    ok &= render_panel(d, {
        "box": (left[0], top_row[0], left[1], top_row[1]),
        "kicker": "THE HAGUE \u00b7 WORLD COURT",
        "colour": NAVY,
        "icon": "scales",
        "headline": "WORLD COURT: MYANMAR COMMITTED GENOCIDE",
        "head_size": 22,
        "body": "Myanmar was found guilty of genocide against the "
                "Rohingya \u2014 the first time any international "
                "court has found a state guilty of genocide.",
        "body_size": 18,
    })
    ok &= render_panel(d, {
        "box": (right_col[0], top_row[0], right_col[1], top_row[1]),
        "kicker": "MARKETS",
        "colour": TEAL,
        "icon": "chart",
        "headline": "AI SELL-OFF: S&P 500 INTO CORRECTION",
        "head_size": 22,
        "body": "The S&P 500 fell 3.7%, the Nasdaq 5.28% and the "
                "Nikkei 5.06%. Anthropic debuted at about a $2 "
                "trillion valuation, then stumbled.",
        "body_size": 18,
    })
    ok &= render_panel(d, {
        "box": (left[0], bot_row[0], left[1], bot_row[1]),
        "kicker": "ANTALYA \u00b7 COP31",
        "colour": GREEN,
        "icon": "leaf",
        "headline": "CLIMATE TALKS PAST DEADLINE",
        "head_size": 22,
        "body": "COP31 ran past its Friday deadline, deadlocked over "
                "fossil fuels. Ukraine blocked a Russian report "
                "with data from occupied Ukrainian land.",
        "body_size": 18,
    })
    ok &= render_panel(d, {
        "box": (right_col[0], bot_row[0], right_col[1], bot_row[1]),
        "kicker": "WASHINGTON \u00b7 CYBER",
        "colour": PURPLE,
        "icon": "lock",
        "headline": "FBI DATABASE HACKED; CYBER CHIEF OUSTED",
        "head_size": 22,
        "body": "The FBI's crime database and the Agriculture "
                "Department were reportedly hacked amid US outages. "
                "Trump ousted the cyber director.",
        "body_size": 18,
    })

    # ---------- wide strip: UK-EU deal ----------
    ok &= render_panel(d, {
        "box": (MARGIN, 766, right, 890),
        "kicker": "BRUSSELS \u00b7 LONDON",
        "colour": SLATE,
        "icon": "stars",
        "headline": "UK AND EU SIGN BIGGEST POST-BREXIT DEALS",
        "head_size": 24,
        "body": "Agri-food trade, carbon markets and youth mobility, "
                "plus a return to Erasmus+.",
        "body_size": 18,
    })

    # ---------- ticker ----------
    d.rectangle([0, 902, W, H], fill=INK)
    d.text((MARGIN, 912), "ALSO TODAY", font=font(SANS_B, 22), fill=GOLD)
    ticker = (
        "Peru quake, magnitude 6.7\u20136.9, shakes the Andes; no "
        "casualties \u2022 Trump weighs new Iran strikes; Iran says "
        "it downed a US MQ-9 drone over Hormuz \u2022 Bayer to pay "
        "$7.25bn to settle Roundup claims \u2022 Trial pill makes "
        "pancreatic tumours undetectable in 1 in 12 patients"
    )
    tf = font(SANS, 20)
    y = 944
    for line in wrap(d, ticker, tf, W - 2 * MARGIN):
        d.text((MARGIN, y), line, font=tf, fill=WHITE)
        y += 26

    img.save("entry.png")
    print("wrote entry.png, all panels fit:", ok)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
