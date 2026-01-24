"""Multicolor bitmap encoder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class MulticolorBitmapResult:
    bitmap: bytes
    screen: bytes
    color: bytes
    background_color: int
    cell_colors: List[Tuple[int, int, int]]
    conflicts: List[Dict[str, object]]
    fixed_cells: int


def _cell_color_counts(
    pixels: List[int],
    width: int,
    cell_x: int,
    cell_y: int,
) -> Dict[int, int]:
    counts: Dict[int, int] = {}
    start_x = cell_x * 4
    start_y = cell_y * 8
    for row in range(8):
        for col in range(4):
            idx = (start_y + row) * width + (start_x + col)
            color = pixels[idx]
            counts[color] = counts.get(color, 0) + 1
    return counts


def encode_bitmap_multicolor(
    pixels: List[int],
    width: int,
    height: int,
    background_color: int,
    strict: bool = False,
) -> MulticolorBitmapResult:
    if width != 160 or height != 200:
        raise ValueError("bitmap_multicolor requires 160x200 input")

    bitmap = bytearray(8000)
    screen = bytearray(1000)
    color = bytearray(1000)
    conflicts: List[Dict[str, object]] = []
    cell_colors: List[Tuple[int, int, int]] = []
    fixed_cells = 0

    for cell_y in range(25):
        for cell_x in range(40):
            counts = _cell_color_counts(pixels, width, cell_x, cell_y)
            colors_sorted = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            colors = [c for c, _ in colors_sorted]
            extra_colors = [
                c for c in colors if c != background_color
            ]
            if len(extra_colors) > 3:
                conflicts.append(
                    {
                        "cell_x": cell_x,
                        "cell_y": cell_y,
                        "colors": colors,
                        "background_color": background_color,
                    }
                )
                if strict:
                    raise ValueError(
                        f"Color conflict in cell ({cell_x},{cell_y}): {colors}"
                    )
                fixed_cells += 1

            selected = [c for c in colors if c != background_color][:3]
            while len(selected) < 3:
                selected.append(background_color)

            color1, color2, color3 = selected
            cell_colors.append((color1, color2, color3))

            screen_idx = cell_y * 40 + cell_x
            screen[screen_idx] = (color2 << 4) | color1
            color[screen_idx] = color3 & 0x0F

            for row in range(8):
                byte_val = 0
                for col in range(4):
                    pixel_index = (
                        (cell_y * 8 + row) * width + (cell_x * 4 + col)
                    )
                    pixel_color = pixels[pixel_index]
                    if pixel_color == background_color:
                        value = 0
                    elif pixel_color == color1:
                        value = 1
                    elif pixel_color == color2:
                        value = 2
                    elif pixel_color == color3:
                        value = 3
                    else:
                        # Fallback to background when conflict remains.
                        value = 0
                    byte_val = (byte_val << 2) | value
                bitmap_index = (cell_y * 8 + row) * 40 + cell_x
                bitmap[bitmap_index] = byte_val

    return MulticolorBitmapResult(
        bitmap=bytes(bitmap),
        screen=bytes(screen),
        color=bytes(color),
        background_color=background_color,
        cell_colors=cell_colors,
        conflicts=conflicts,
        fixed_cells=fixed_cells,
    )
