"""Palette mapping helpers for VIC-II colors."""

from __future__ import annotations

from typing import Iterable, List, Tuple

from PIL import Image

from .constants import VIC_II_PALETTE


def palette_colors() -> List[Tuple[int, int, int]]:
    return [entry["rgb"] for entry in VIC_II_PALETTE]


def nearest_color_index(rgb: Tuple[int, int, int]) -> int:
    r, g, b = rgb
    best_index = 0
    best_dist = float("inf")
    for entry in VIC_II_PALETTE:
        pr, pg, pb = entry["rgb"]
        dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if dist < best_dist:
            best_dist = dist
            best_index = entry["index"]
    return best_index


def build_palette_image() -> Image.Image:
    palette = []
    for entry in VIC_II_PALETTE:
        palette.extend(entry["rgb"])
    palette += [0] * (256 * 3 - len(palette))
    pal_img = Image.new("P", (16, 16))
    pal_img.putpalette(palette)
    return pal_img


def map_image_to_palette(
    image: Image.Image,
    dither: bool = False,
) -> Tuple[List[int], int, int]:
    """Map an image to VIC-II palette indices.

    Returns (palette_indices, width, height).
    """
    img = image.convert("RGB")
    width, height = img.size
    if dither:
        pal_img = build_palette_image()
        quantized = img.quantize(palette=pal_img, dither=Image.FLOYDSTEINBERG)
        return list(quantized.getdata()), width, height

    pixels = list(img.getdata())
    indices = [nearest_color_index(rgb) for rgb in pixels]
    return indices, width, height


def image_from_indices(
    indices: Iterable[int],
    width: int,
    height: int,
) -> Image.Image:
    palette = build_palette_image()
    img = Image.new("P", (width, height))
    img.putpalette(palette.getpalette())
    img.putdata(list(indices))
    return img
