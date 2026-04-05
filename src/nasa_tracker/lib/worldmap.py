"""
worldmap.py — Compact world land mask for terminal rendering
============================================================

Source:  Natural Earth 50m land polygons (public domain)
         https://www.naturalearthdata.com/

Two resolutions are embedded:
  MASK_360x180  : 1° per cell,  360×180  grid  (2504 base64 chars → 1878 bytes compressed)
  MASK_720x360  : 0.5° per cell, 720×360 grid  (6428 base64 chars → 4820 bytes compressed)

Both are stored as zlib-compressed, base64-encoded, 1-bit-per-cell grids.
Row 0 = 90°N, col 0 = 180°W.  1 = land, 0 = ocean.

Dependencies: stdlib only (base64, zlib, struct) — numpy optional for bulk use.

Usage:
    from worldmap import is_land, get_mask, ascii_preview

    # Point query (no numpy needed)
    is_land(51.5, -0.1)          # True  (London)
    is_land(0, -30)               # False (Atlantic Ocean)

    # Get full numpy mask array
    mask = get_mask(resolution=720)   # shape (360, 720)

    # ASCII preview in terminal
    ascii_preview()
"""

import base64
import zlib
import struct

# ---------------------------------------------------------------------------
# Embedded land mask data (Natural Earth 50m, zlib+base64, 1-bit per cell)
# ---------------------------------------------------------------------------

_DATA_360x180 = (
        "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"
)

_DATA_720x360 = (
        "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"
)

# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

_cache: dict = {}

def get_mask(resolution: int = 720):
    """
    Return a 2D list (or numpy array if numpy is available) of 0/1 values.
    resolution: 360 → shape (180, 360) at 1°/cell
                720 → shape (360, 720) at 0.5°/cell
    Row 0 = 90°N, col 0 = 180°W.
    """
    if resolution in _cache:
        return _cache[resolution]

    if resolution == 360:
        raw_b64, W, H = _DATA_360x180, 360, 180
    elif resolution == 720:
        raw_b64, W, H = _DATA_720x360, 720, 360
    else:
        raise ValueError(f"resolution must be 360 or 720, got {resolution}")

    raw = zlib.decompress(base64.b64decode(raw_b64))
    n_bytes = (W * H + 7) // 8
    # Unpack bits row-major
    mask = []
    bit_pos = 0
    byte_idx = 0
    byte = raw[0] if raw else 0
    for r in range(H):
        row = []
        for c in range(W):
            row.append((byte >> (7 - bit_pos)) & 1)
            bit_pos += 1
            if bit_pos == 8:
                bit_pos = 0
                byte_idx += 1
                if byte_idx < len(raw):
                    byte = raw[byte_idx]
        mask.append(row)

    # Use numpy if available for faster downstream use
    try:
        import numpy as np
        mask = np.array(mask, dtype=np.uint8)
    except ImportError:
        pass

    _cache[resolution] = mask
    return mask


def is_land(lat: float, lon: float, resolution: int = 720) -> bool:
    """
    Return True if the given lat/lon is on land (1° or 0.5° cell resolution).

    lat: -90 to 90   (positive = North)
    lon: -180 to 180 (positive = East)
    resolution: 360 or 720 (default 720 for better coastal accuracy)
    """
    if resolution == 720:
        W, H = 720, 360
    else:
        W, H = 360, 180

    row = int((90.0 - lat) / 180.0 * H)
    col = int((lon + 180.0) / 360.0 * W)
    row = max(0, min(H - 1, row))
    col = max(0, min(W - 1, col))

    mask = get_mask(resolution)
    try:
        return bool(mask[row, col])   # numpy
    except TypeError:
        return bool(mask[row][col])   # plain list


def latlon_to_cell(lat: float, lon: float, W: int, H: int):
    """Convert lat/lon to (row, col) grid indices for a W×H mask."""
    row = int((90.0 - lat) / 180.0 * H)
    col = int((lon + 180.0) / 360.0 * W)
    return max(0, min(H - 1, row)), max(0, min(W - 1, col))


def cell_to_latlon(row: int, col: int, W: int, H: int):
    """Return the centre lat/lon of a grid cell."""
    lat = 90.0 - (row + 0.5) / H * 180.0
    lon = -180.0 + (col + 0.5) / W * 360.0
    return lat, lon


# ---------------------------------------------------------------------------
# Terminal rendering helpers
# ---------------------------------------------------------------------------

# Unicode half-block chars for 2-rows-per-char rendering
# Top pixel set, bottom pixel set:
#   (0,0) → space   (1,0) → ▀   (0,1) → ▄   (1,1) → █
_HALF_BLOCKS = {
    (0, 0): ' ',
    (1, 0): '▀',
    (0, 1): '▄',
    (1, 1): '█',
}


def render_map(
    width: int = 120,
    height: int = None,
    iss_lat: float = None,
    iss_lon: float = None,
    extra_points: list = None,
    land_char: str = None,
    sea_char: str = None,
    use_half_blocks: bool = True,
) -> str:
    """
    Render a world map as a Unicode string suitable for terminal output.

    Parameters
    ----------
    width           Terminal columns (default 120).
    height          Terminal rows to use.  If None, derived from width with 1:2
                    aspect ratio (half-blocks give 2 pixel rows per char row).
    iss_lat/lon     If given, plot the ISS position as ✛.
    extra_points    List of (lat, lon, char) tuples for additional markers.
    land_char       Override land character (single char, disables half-blocks).
    sea_char        Override sea character (single char, disables half-blocks).
    use_half_blocks Use ▀▄█ for sub-row resolution (default True).

    Returns
    -------
    Multi-line string ready for print().
    """
    extra_points = extra_points or []

    if use_half_blocks and land_char is None and sea_char is None:
        # Each character cell covers 2 pixel rows
        px_W = width
        px_H = (height * 2) if height else (width // 2)
        # Snap to even
        if px_H % 2 != 0:
            px_H += 1
        char_H = px_H // 2
    else:
        px_W = width
        px_H = height or (width // 4)
        char_H = px_H
        use_half_blocks = False

    # Build pixel grid from mask (downsample 720x360 to px_W × px_H)
    mask = get_mask(720)
    MASK_W, MASK_H = 720, 360

    def sample(px_row, px_col):
        mr = int(px_row / px_H * MASK_H)
        mc = int(px_col / px_W * MASK_W)
        mr = max(0, min(MASK_H - 1, mr))
        mc = max(0, min(MASK_W - 1, mc))
        try:
            return int(mask[mr, mc])
        except TypeError:
            return int(mask[mr][mc])

    # Build overlay grid for markers
    overlay = {}   # (px_row, px_col) → char

    def place(lat, lon, ch):
        px_row = int((90.0 - lat) / 180.0 * px_H)
        px_col = int((lon + 180.0) / 360.0 * px_W)
        px_row = max(0, min(px_H - 1, px_row))
        px_col = max(0, min(px_W - 1, px_col))
        overlay[(px_row, px_col)] = ch

    if iss_lat is not None and iss_lon is not None:
        place(iss_lat, iss_lon, '✛')
    for lat, lon, ch in extra_points:
        place(lat, lon, ch)

    # Render
    lines = []
    if use_half_blocks:
        for char_r in range(char_H):
            pr_top = char_r * 2
            pr_bot = char_r * 2 + 1
            row_chars = []
            for pc in range(px_W):
                # Check overlay on either pixel row of this char cell
                if (pr_top, pc) in overlay:
                    row_chars.append(overlay[(pr_top, pc)])
                elif (pr_bot, pc) in overlay:
                    row_chars.append(overlay[(pr_bot, pc)])
                else:
                    top = sample(pr_top, pc)
                    bot = sample(pr_bot, pc)
                    row_chars.append(_HALF_BLOCKS[(top, bot)])
            lines.append(''.join(row_chars))
    else:
        lc = land_char or '#'
        sc = sea_char  or '.'
        for pr in range(px_H):
            row_chars = []
            for pc in range(px_W):
                if (pr, pc) in overlay:
                    row_chars.append(overlay[(pr, pc)])
                else:
                    row_chars.append(lc if sample(pr, pc) else sc)
            lines.append(''.join(row_chars))

    return '\n'.join(lines)


def ascii_preview(width: int = 90) -> None:
    """Quick ASCII preview using # and . characters."""
    print(render_map(width=width, use_half_blocks=False, land_char='#', sea_char='.'))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    iss_lat = iss_lon = None
    if len(sys.argv) >= 3:
        try:
            iss_lat, iss_lon = float(sys.argv[1]), float(sys.argv[2])
        except ValueError:
            pass

    # Try half-block render first
    print(render_map(width=120, iss_lat=iss_lat, iss_lon=iss_lon))
    if iss_lat is not None:
        print(f"ISS: {iss_lat:.2f}°, {iss_lon:.2f}°  land={is_land(iss_lat, iss_lon)}")
