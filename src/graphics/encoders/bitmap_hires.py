"""Hires bitmap encoder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class HiresBitmapResult:
    bitmap: bytes
    screen: bytes
    color: bytes
    cell_colors: List[Tuple[int, int]]
    conflicts: List[Dict[str, object]]
    fixed_cells: int


def _cell_color_counts(
    pixels: List[int],
    width: int,
    cell_x: int,
    cell_y: int,
) -> Dict[int, int]:
    counts: Dict[int, int] = {}
    start_x = cell_x * 8
    start_y = cell_y * 8
    for row in range(8):
        for col in range(8):
            idx = (start_y + row) * width + (start_x + col)
            color = pixels[idx]
            counts[color] = counts.get(color, 0) + 1
    return counts


def encode_bitmap_hires(
    pixels: List[int],
    width: int,
    height: int,
    strict: bool = False,
) -> HiresBitmapResult:
    if width != 320 or height != 200:
        raise ValueError("bitmap_hires requires 320x200 input")

    bitmap = bytearray(8000)
    screen = bytearray(1000)
    color = bytearray(1000)
    conflicts: List[Dict[str, object]] = []
    cell_colors: List[Tuple[int, int]] = []
    fixed_cells = 0

    for cell_y in range(25):
        for cell_x in range(40):
            counts = _cell_color_counts(pixels, width, cell_x, cell_y)
            colors_sorted = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            colors = [c for c, _ in colors_sorted]
            if len(colors) > 2:
                conflicts.append(
                    {
                        "cell_x": cell_x,
                        "cell_y": cell_y,
                        "colors": colors,
                    }
                )
                if strict:
                    raise ValueError(
                        f"Color conflict in cell ({cell_x},{cell_y}): {colors}"
                    )
                fixed_cells += 1

            color0 = colors[0] if colors else 0
            color1 = colors[1] if len(colors) > 1 else color0
            cell_colors.append((color0, color1))

            screen_idx = cell_y * 40 + cell_x
            screen[screen_idx] = (color1 << 4) | color0

            for row in range(8):
                byte_val = 0
                for col in range(8):
                    pixel_index = (
                        (cell_y * 8 + row) * width + (cell_x * 8 + col)
                    )
                    pixel_color = pixels[pixel_index]
                    value = 1 if pixel_color == color1 else 0
                    byte_val = (byte_val << 1) | value
                bitmap_index = (cell_y * 8 + row) * 40 + cell_x
                bitmap[bitmap_index] = byte_val

    return HiresBitmapResult(
        bitmap=bytes(bitmap),
        screen=bytes(screen),
        color=bytes(color),
        cell_colors=cell_colors,
        conflicts=conflicts,
        fixed_cells=fixed_cells,
    )
