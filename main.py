#!/usr/bin/env python3
"""Entry program for make.fun's news-image-20261121 bounty (Python 3.13,
standard library only).

The repository ships one finished image, entry.png: a newspaper front
page, drawn by generate_image.py, that sums up the world news of
Saturday 21 November 2026. This program is its gatekeeper. It reads
the image, proves the file satisfies the contest gate -- PNG or JPEG
by its first bytes, at most 1 MiB, at most 1024x1024 pixels, and whole
(every PNG chunk present with a correct checksum, or every JPEG
segment through to the end marker) -- then copies it into the output
directory and reads the copy back to prove the bytes that land there
are exactly the bytes that were validated.

Run it the way the grader does:

    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

MAX_BYTES = 1_048_576  # 1 MiB
MAX_SIDE = 1024

ROOT = Path(__file__).resolve().parent
IMAGE = ROOT / "entry.png"


def fail(why):
    raise SystemExit(f"entry.png rejected: {why}")


def png_dimensions(blob):
    """Walk the whole PNG chunk chain, verifying every CRC, and
    return (width, height) from the IHDR chunk."""
    if len(blob) < 8 + 25:
        fail("too short to hold a signature and an IHDR chunk")
    offset = 8  # the 8-byte signature was matched by the caller
    size = None
    while offset < len(blob):
        if offset + 12 > len(blob):
            fail(f"chunk at offset {offset} is cut short")
        (length,) = struct.unpack_from(">I", blob, offset)
        kind = blob[offset + 4:offset + 8]
        stop = offset + 12 + length
        if stop > len(blob):
            fail(f"chunk {kind!r} at offset {offset} runs past the file end")
        payload = blob[offset + 8:offset + 8 + length]
        (crc,) = struct.unpack_from(">I", blob, offset + 8 + length)
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != crc:
            fail(f"chunk {kind!r} at offset {offset} fails its CRC check")
        if size is None:
            if kind != b"IHDR" or length != 13:
                fail("the first chunk is not a 13-byte IHDR")
            size = struct.unpack(">II", payload[:8])
        if kind == b"IEND":
            if length != 0:
                fail("the IEND chunk carries data")
            if stop != len(blob):
                fail("bytes follow the IEND chunk")
            return size
        offset = stop
    fail("no IEND chunk found")


def jpeg_dimensions(blob):
    """Walk JPEG segments to the first Start Of Frame; return its size."""
    if blob[-2:] != b"\xff\xd9":
        fail("the file does not end with the JPEG EOI marker")
    offset = 2  # the SOI marker was matched by the caller
    while offset + 4 <= len(blob):
        if blob[offset] != 0xFF:
            fail(f"segment at offset {offset} has no marker prefix")
        marker = blob[offset + 1]
        (seg_len,) = struct.unpack_from(">H", blob, offset + 2)
        is_frame = 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC)
        if is_frame:
            height, width = struct.unpack_from(">HH", blob, offset + 5)
            return width, height
        offset += 2 + seg_len
    fail("no Start Of Frame segment found")


def main():
    blob = IMAGE.read_bytes()
    if not blob:
        fail("the file is empty")
    if len(blob) > MAX_BYTES:
        fail(f"{len(blob)} bytes exceeds the {MAX_BYTES}-byte limit")

    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        fmt = "PNG"
        width, height = png_dimensions(blob)
    elif blob[:3] == b"\xff\xd8\xff":
        fmt = "JPEG"
        width, height = jpeg_dimensions(blob)
    else:
        fail("the first bytes are neither the PNG signature nor a JPEG SOI")

    if width < 1 or height < 1:
        fail(f"implausible dimensions {width}x{height}")
    if width > MAX_SIDE or height > MAX_SIDE:
        fail(f"{width}x{height} exceeds the {MAX_SIDE}x{MAX_SIDE} limit")

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "entry.png"
    shutil.copyfile(IMAGE, dest)

    if dest.read_bytes() != blob:
        fail("the copy in the output directory differs from the source")

    print(
        f"entry.png OK: {fmt} {width}x{height}, {len(blob)} bytes, "
        f"sha256 {hashlib.sha256(blob).hexdigest()}, copied to {dest} "
        "and verified byte for byte"
    )


if __name__ == "__main__":
    sys.exit(main())
