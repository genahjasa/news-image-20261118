"""news-image-20261118: write the entry image to /output/entry.png.

The entry image is a 1024x1024 front-page collage summing up the world news
of Wednesday 18 November 2026: Xi greeting Trump on the tarmac in Shenzhen
as APEC opens ahead of Thursday's three-way talks with Putin, US jets
striking Iran's Qeshm Island as Iran hits back at Bahrain and Kuwait, the
Kerch Bridge hit for a second day with part of its road span down, and
Democrat Mary Peltola winning Alaska's Senate seat for a 56-44 Democratic
majority. Pure stdlib, no network, deterministic: both runs write the same
bytes. Before copying, the source is validated as a JPEG of exactly
1024x1024 (SOI magic, SOF dimensions parsed with pure stdlib). After
copying, the output is verified byte-for-byte against the source (sha256)
and a one-line summary is printed; a missing source, a bad image, or a
mismatched copy exits non-zero with a clear error.
"""
import hashlib
import os
import shutil
import struct
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image.jpg")
DST = "/output/entry.png"
EXPECT_W, EXPECT_H = 1024, 1024


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def jpeg_dimensions(path):
    """Return (width, height) of a JPEG, or None if it is not a valid JPEG."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 3 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):  # SOF0/SOF1/SOF2: baseline/extended
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        i += 2 + seg_len
    return None


def main():
    if not os.path.isfile(SRC):
        print(f"error: source image missing: {SRC}", file=sys.stderr)
        return 1
    dims = jpeg_dimensions(SRC)
    if dims is None:
        print(f"error: source is not a valid JPEG: {SRC}", file=sys.stderr)
        return 1
    if dims != (EXPECT_W, EXPECT_H):
        print(f"error: source is {dims[0]}x{dims[1]}, expected "
              f"{EXPECT_W}x{EXPECT_H}: {SRC}", file=sys.stderr)
        return 1
    os.makedirs("/output", exist_ok=True)
    shutil.copyfile(SRC, DST)
    src_hash, dst_hash = sha256(SRC), sha256(DST)
    if src_hash != dst_hash:
        print(f"error: copy mismatch: {DST} != {SRC}", file=sys.stderr)
        return 1
    print(f"wrote {DST}: {os.path.getsize(DST)} bytes, sha256 {dst_hash[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
