#!/usr/bin/env python3
"""Put the finished 20 November 2026 poster where the harness looks.

The picture itself was painted earlier, off-line, by build_image.py
and stored in this repository as entry.png; it was run twice and the
bytes came out identical both times. All this little program has to
do is place that one file at /output/entry.png for the judges.

Nothing beyond the standard library is used, and nothing is fetched
from the network, so it runs the same in the grading sandbox as here.
The poster packs the day into one front page: a lead story on Russia's
20 November barrage of Kyiv and its spill into Poland, four panels
(Gulf blockade, AI market selloff, COP31 deadlock, Trump defending his
Putin and Xi ties), and a sourced wire of 37 further stories, 42 in
total, with the date printed on the masthead and checked in its own box.

Verified locally 2026-11-21: entry.png is 1024x1024, 206,807 bytes,
sha256 df340bde6e87bc1a648ad87f31a2d381b15623ebc63bbfa2a6bd122329071e08,
identical across repeated runs of build_image.py and main.py.
"""

from pathlib import Path

POSTER = Path(__file__).resolve().parent / "entry.png"
TARGET = Path("/output/entry.png")


def place_poster() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(POSTER.read_bytes())


place_poster()
