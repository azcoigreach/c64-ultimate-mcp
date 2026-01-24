"""Sprite encoder for hires and multicolor sprites."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SpriteResult:
    data: bytes
    width: int
    height: int
    palette_indexes: List[int]
    conflicts: List[Dict[str, object]]
    primary_color: int
    extra_colors: List[int]


def encode_sprite_hires(
    pixels: List[int],
    width: int,
    height: int,
    strict: bool = False,
) -> SpriteResult:
    if width != 24 or height != 21:
        raise ValueError("hires sprites require 24x21 input")

    counts: Dict[int, int] = {}
    for color in pixels:
        counts[color] = counts.get(color, 0) + 1
    colors_sorted = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    colors = [c for c, _ in colors_sorted]
    conflicts = []
    if len(colors) > 2:
        conflicts.append({"colors": colors})
        if strict:
            raise ValueError(f"Sprite color conflict: {colors}")
    color0 = colors[0] if colors else 0
    color1 = colors[1] if len(colors) > 1 else color0

    data = bytearray(64)
    byte_index = 0
    for row in range(height):
        row_bytes = 0
        for col in range(width):
            pixel_color = pixels[row * width + col]
            bit = 1 if pixel_color == color1 else 0
            row_bytes = (row_bytes << 1) | bit
            if (col + 1) % 8 == 0:
                data[byte_index] = row_bytes
                byte_index += 1
                row_bytes = 0

    return SpriteResult(
        data=bytes(data),
        width=width,
        height=height,
        palette_indexes=colors,
        conflicts=conflicts,
        primary_color=color1,
        extra_colors=[color0],
    )


def encode_sprite_multicolor(
    pixels: List[int],
    width: int,
    height: int,
    background_color: int,
    strict: bool = False,
) -> SpriteResult:
    if width != 12 or height != 21:
        raise ValueError("multicolor sprites require 12x21 input")

    counts: Dict[int, int] = {}
    for color in pixels:
        counts[color] = counts.get(color, 0) + 1
    colors_sorted = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    colors = [c for c, _ in colors_sorted]
    extra_colors = [c for c in colors if c != background_color]
    conflicts = []
    if len(extra_colors) > 3:
        conflicts.append({"colors": colors, "background_color": background_color})
        if strict:
            raise ValueError(f"Sprite color conflict: {colors}")

    selected = [c for c in colors if c != background_color][:3]
    while len(selected) < 3:
        selected.append(background_color)

    color1, color2, color3 = selected

    data = bytearray(64)
    byte_index = 0
    for row in range(height):
        for col in range(0, width, 4):
            byte_val = 0
            for pixel in range(4):
                pixel_color = pixels[row * width + (col + pixel)]
                if pixel_color == background_color:
                    value = 0
                elif pixel_color == color1:
                    value = 1
                elif pixel_color == color2:
                    value = 2
                elif pixel_color == color3:
                    value = 3
                else:
                    value = 0
                byte_val = (byte_val << 2) | value
            data[byte_index] = byte_val
            byte_index += 1

    return SpriteResult(
        data=bytes(data),
        width=width,
        height=height,
        palette_indexes=colors,
        conflicts=conflicts,
        primary_color=color3,
        extra_colors=[color1, color2, background_color],
    )
