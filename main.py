"""news-image-20261118 -- front-page collage of the world news of
Wednesday 18 November 2026.

The artwork (image.jpg, 1024x1024) sums up the day in one frame:
Xi greeting Trump on the tarmac in Shenzhen as APEC opens ahead of
Thursday's three-way talks with Putin; US jets striking Iran's Qeshm
Island as Iran hits back in Bahrain and Kuwait; the Kerch Bridge hit
for a second day with part of its road span down; and Democrat Mary
Peltola winning Alaska's Senate seat for a 56-44 Democratic majority.

This script is the program/v1 harness entry point. It does no network
access and no image manipulation: it locates the collage next to
itself, validates that it really is a 1024x1024 JPEG, and copies it
byte-for-byte to /output/entry.png, verifying the copy with sha256.
"""

import hashlib
import os
import struct
import sys

EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
SOURCE_NAME = "image.jpg"
OUTPUT_PATH = "/output/entry.png"

# JPEG SOF markers that carry the image dimensions (baseline,
# extended sequential, progressive, and lossless variants).
SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
               0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def fail(message):
    """Print an error to stderr and exit non-zero."""
    print("error: %s" % message, file=sys.stderr)
    sys.exit(1)


def jpeg_dimensions(data):
    """Return (width, height) parsed from a JPEG byte string.

    Checks the SOI magic, then walks the marker segments until a SOF
    segment is found and reads its dimensions with struct. Raises
    ValueError if the data is not a well-formed JPEG with a SOF.
    """
    if len(data) < 3 or data[0:2] != b"\xff\xd8":
        raise ValueError("missing JPEG SOI magic bytes (not a JPEG file)")
    if data[2] != 0xFF:
        raise ValueError("malformed JPEG marker after SOI")

    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            raise ValueError("expected JPEG marker at offset %d" % offset)
        marker = data[offset + 1]
        # Padding bytes and restart markers have no length field.
        if marker == 0xFF:
            offset += 1
            continue
        if marker == 0x00 or 0xD0 <= marker <= 0xD7:
            offset += 2
            continue
        if marker == 0xD8:  # nested SOI, skip it
            offset += 2
            continue
        if marker == 0xD9:  # EOI reached without a SOF segment
            break
        if offset + 4 > len(data):
            break
        length = struct.unpack(">H", data[offset + 2:offset + 4])[0]
        if length < 2 or offset + 2 + length > len(data):
            raise ValueError("truncated JPEG segment at offset %d" % offset)
        if marker in SOF_MARKERS:
            # SOF layout: precision (1 byte), height (2), width (2).
            height, width = struct.unpack(
                ">HH", data[offset + 5:offset + 9])
            return width, height
        offset += 2 + length
    raise ValueError("no SOF segment found (not a valid JPEG image)")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)

    if not os.path.isfile(source):
        fail("source image not found: %s" % source)

    try:
        with open(source, "rb") as handle:
            payload = handle.read()
    except OSError as exc:
        fail("cannot read %s: %s" % (source, exc))

    if not payload:
        fail("%s is empty (0 bytes)" % SOURCE_NAME)

    try:
        width, height = jpeg_dimensions(payload)
    except ValueError as exc:
        fail("%s is not a valid JPEG: %s" % (SOURCE_NAME, exc))

    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        fail("%s is %dx%d, expected %dx%d"
             % (SOURCE_NAME, width, height, EXPECTED_WIDTH, EXPECTED_HEIGHT))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    try:
        with open(OUTPUT_PATH, "wb") as handle:
            handle.write(payload)
    except OSError as exc:
        fail("cannot write %s: %s" % (OUTPUT_PATH, exc))

    digest = hashlib.sha256(payload).hexdigest()
    try:
        with open(OUTPUT_PATH, "rb") as handle:
            copied = handle.read()
    except OSError as exc:
        fail("cannot re-read %s for verification: %s" % (OUTPUT_PATH, exc))
    if hashlib.sha256(copied).hexdigest() != digest:
        fail("copy mismatch: /output/entry.png does not match image.jpg")

    print("wrote %s (%d bytes, sha256 %s)"
          % (OUTPUT_PATH, len(payload), digest[:16]))


if __name__ == "__main__":
    main()
