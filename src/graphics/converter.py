"""Graphics conversion pipeline for C64 assets."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from PIL import Image

from .constants import BITMAP_MODES, DEFAULT_ADDRESSES, SPRITE_MODES, VIC_II_PALETTE
from .encoders.bitmap_hires import encode_bitmap_hires
from .encoders.bitmap_multicolor import encode_bitmap_multicolor
from .encoders.sprite import encode_sprite_hires, encode_sprite_multicolor
from .manifest import Manifest
from .palette import map_image_to_palette
from .report import build_report_text, serialize_report_json
from .emitters.asm import build_bitmap_asm_include, build_sprite_asm_include
from .emitters.basic import build_bitmap_basic_loader, build_sprite_basic_loader


def _ensure_output_dir(output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)


def _load_image(input_path: str) -> Image.Image:
    image = Image.open(input_path)
    if image.format not in ("PNG", "JPEG", "BMP"):
        raise ValueError(f"Unsupported image format: {image.format}")
    return image


def _resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
    if image.size == (width, height):
        return image
    return image.resize((width, height), Image.LANCZOS)


def _palette_used(indices: List[int]) -> List[int]:
    return sorted(set(indices))


def _palette_entries(indices: List[int]) -> List[Dict[str, Any]]:
    return [entry for entry in VIC_II_PALETTE if entry["index"] in indices]


def _default_background(indices: List[int]) -> int:
    counts: Dict[int, int] = {}
    for idx in indices:
        counts[idx] = counts.get(idx, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _vic_registers_for_bitmap(
    mode: str,
    addresses: Dict[str, int],
) -> Dict[str, str]:
    screen_base = (addresses["screen"] // 0x0400) & 0x0F
    bitmap_base = (addresses["bitmap"] // 0x2000) & 0x07
    d018 = (screen_base << 4) | (bitmap_base << 1)
    d011 = 0x1B | 0x20
    d016 = 0x18 if mode == "bitmap_multicolor" else 0x08
    return {
        "d011": f"${d011:02X}",
        "d016": f"${d016:02X}",
        "d018": f"${d018:02X}",
    }


def _write_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def convert_bitmap(
    input_path: str,
    mode: str,
    output_dir: str,
    addresses: Optional[Dict[str, int]] = None,
    dither: bool = False,
    background_color: Optional[int] = None,
    border_color: Optional[int] = None,
    strict: bool = False,
    emit_asm: bool = False,
    emit_basic: bool = False,
) -> Dict[str, Any]:
    if mode not in BITMAP_MODES:
        raise ValueError(f"Unsupported bitmap mode: {mode}")

    addr = dict(DEFAULT_ADDRESSES)
    if addresses:
        for key, value in addresses.items():
            if isinstance(value, str):
                addr[key] = int(value, 0)
            else:
                addr[key] = int(value)

    image = _load_image(input_path)
    target = BITMAP_MODES[mode]
    image = _resize_image(image, target["width"], target["height"])
    indices, width, height = map_image_to_palette(image, dither=dither)
    palette_used = _palette_used(indices)
    background = background_color if background_color is not None else _default_background(indices)

    if mode == "bitmap_multicolor":
        result = encode_bitmap_multicolor(
            indices,
            width,
            height,
            background_color=background,
            strict=strict,
        )
        bitmap = result.bitmap
        screen = result.screen
        color = result.color
        conflicts = result.conflicts
        fixed_cells = result.fixed_cells
    else:
        result = encode_bitmap_hires(
            indices,
            width,
            height,
            strict=strict,
        )
        bitmap = result.bitmap
        screen = result.screen
        color = result.color
        conflicts = result.conflicts
        fixed_cells = result.fixed_cells

    _ensure_output_dir(output_dir)
    bitmap_path = os.path.join(output_dir, "bitmap.bin")
    screen_path = os.path.join(output_dir, "screen.bin")
    color_path = os.path.join(output_dir, "color.bin")
    with open(bitmap_path, "wb") as handle:
        handle.write(bitmap)
    with open(screen_path, "wb") as handle:
        handle.write(screen)
    with open(color_path, "wb") as handle:
        handle.write(color)

    report = {
        "mode": mode,
        "image_size": [width, height],
        "palette_used": palette_used,
        "background_color": background,
        "conflicts": conflicts,
        "fixed_cells": fixed_cells,
    }
    report_json = serialize_report_json(report)
    report_text = build_report_text(report)
    report_json_path = os.path.join(output_dir, "report.json")
    report_txt_path = os.path.join(output_dir, "report.txt")
    _write_text(report_json_path, report_json)
    _write_text(report_txt_path, report_text)

    vic_registers = _vic_registers_for_bitmap(mode, addr)
    manifest = Manifest(
        mode=mode,
        addresses=addr,
        output_files={
            "bitmap": os.path.basename(bitmap_path),
            "screen": os.path.basename(screen_path),
            "color": os.path.basename(color_path),
            "report_json": os.path.basename(report_json_path),
            "report_txt": os.path.basename(report_txt_path),
        },
        palette={
            "used_indexes": palette_used,
            "entries": _palette_entries(palette_used),
            "background_color": background,
            "border_color": border_color,
            "color_ram_nibble": "low",
        },
        vic_registers=vic_registers,
        notes="color.bin uses low nibble for color RAM values.",
    )
    manifest_path = os.path.join(output_dir, "manifest.json")
    _write_text(manifest_path, json.dumps(manifest.to_dict(), indent=2))

    asm_path = None
    basic_path = None
    if emit_asm:
        asm_content = build_bitmap_asm_include(manifest.to_dict())
        asm_path = os.path.join(output_dir, "bitmap.inc")
        _write_text(asm_path, asm_content)
    if emit_basic:
        basic_content = build_bitmap_basic_loader(manifest.to_dict(), bitmap, screen, color)
        basic_path = os.path.join(output_dir, "loader.bas")
        _write_text(basic_path, basic_content)

    result_payload = {
        "files": {
            "bitmap": bitmap_path,
            "screen": screen_path,
            "color": color_path,
            "manifest": manifest_path,
            "report_json": report_json_path,
            "report_txt": report_txt_path,
        },
        "report": report,
        "manifest": manifest.to_dict(),
    }
    if asm_path:
        result_payload["files"]["asm_include"] = asm_path
    if basic_path:
        result_payload["files"]["basic_loader"] = basic_path
    return result_payload


def analyze_image(
    input_path: str,
    mode: str,
    constraints_only: bool = False,
    background_color: Optional[int] = None,
    dither: bool = False,
) -> Dict[str, Any]:
    if mode not in BITMAP_MODES:
        raise ValueError(f"Unsupported mode: {mode}")
    target = BITMAP_MODES[mode]
    image = _load_image(input_path)
    image = _resize_image(image, target["width"], target["height"])
    indices, width, height = map_image_to_palette(image, dither=dither)
    background = background_color if background_color is not None else _default_background(indices)

    if mode == "bitmap_multicolor":
        result = encode_bitmap_multicolor(
            indices,
            width,
            height,
            background_color=background,
            strict=False,
        )
        conflicts = result.conflicts
        fixed_cells = result.fixed_cells
    else:
        result = encode_bitmap_hires(
            indices,
            width,
            height,
            strict=False,
        )
        conflicts = result.conflicts
        fixed_cells = result.fixed_cells

    report = {
        "mode": mode,
        "image_size": [width, height],
        "palette_used": [] if constraints_only else _palette_used(indices),
        "background_color": background,
        "conflicts": conflicts,
        "fixed_cells": fixed_cells,
    }
    return {
        "report": report,
        "report_text": build_report_text(report),
    }


def _region_list_from_image(
    image: Image.Image,
    sprite_width: int,
    sprite_height: int,
    regions: Optional[List[Dict[str, int]]] = None,
) -> List[Tuple[int, int, int, int]]:
    if regions:
        return [(r["x"], r["y"], r["w"], r["h"]) for r in regions]

    if image.width == sprite_width and image.height == sprite_height:
        return [(0, 0, sprite_width, sprite_height)]

    if image.width % sprite_width == 0 and image.height % sprite_height == 0:
        tiles = []
        for y in range(0, image.height, sprite_height):
            for x in range(0, image.width, sprite_width):
                tiles.append((x, y, sprite_width, sprite_height))
        return tiles

    raise ValueError("Image size does not align to sprite grid; provide regions.")


def convert_sprites(
    input_path: str,
    sprite_mode: str,
    output_dir: str,
    regions: Optional[List[Dict[str, int]]] = None,
    background_color: Optional[int] = None,
    dither: bool = False,
    strict: bool = False,
    emit_asm: bool = False,
    emit_basic: bool = False,
) -> Dict[str, Any]:
    if sprite_mode not in SPRITE_MODES:
        raise ValueError(f"Unsupported sprite mode: {sprite_mode}")

    image = _load_image(input_path)
    target = SPRITE_MODES[sprite_mode]
    region_list = _region_list_from_image(image, target["width"], target["height"], regions)

    _ensure_output_dir(output_dir)

    sprite_files = []
    sprite_meta = []
    all_conflicts: List[Dict[str, Any]] = []
    for idx, (x, y, w, h) in enumerate(region_list):
        crop = image.crop((x, y, x + w, y + h))
        crop = _resize_image(crop, target["width"], target["height"])
        indices, width, height = map_image_to_palette(crop, dither=dither)
        background = background_color if background_color is not None else _default_background(indices)

        if sprite_mode == "multicolor":
            result = encode_sprite_multicolor(
                indices,
                width,
                height,
                background_color=background,
                strict=strict,
            )
        else:
            result = encode_sprite_hires(
                indices,
                width,
                height,
                strict=strict,
            )

        filename = f"sprite_{idx:03d}.bin"
        sprite_path = os.path.join(output_dir, filename)
        with open(sprite_path, "wb") as handle:
            handle.write(result.data)
        sprite_files.append(sprite_path)

        meta = {
            "index": idx,
            "file": filename,
            "region": {"x": x, "y": y, "w": w, "h": h},
            "palette_used": result.palette_indexes,
            "primary_color": result.primary_color,
            "extra_colors": result.extra_colors,
            "conflicts": result.conflicts,
        }
        sprite_meta.append(meta)
        if result.conflicts:
            all_conflicts.append({"index": idx, "conflicts": result.conflicts})

    positions_path = os.path.join(output_dir, "sprite_positions.json")
    _write_text(positions_path, json.dumps(sprite_meta, indent=2))

    manifest = {
        "mode": f"sprite_{sprite_mode}",
        "output_files": [os.path.basename(path) for path in sprite_files],
        "sprite_positions": os.path.basename(positions_path),
        "conflicts": all_conflicts,
    }
    manifest_path = os.path.join(output_dir, "sprite_manifest.json")
    _write_text(manifest_path, json.dumps(manifest, indent=2))

    asm_path = None
    basic_path = None
    if emit_asm:
        asm_content = build_sprite_asm_include(manifest, sprite_meta)
        asm_path = os.path.join(output_dir, "sprites.inc")
        _write_text(asm_path, asm_content)
    if emit_basic:
        basic_content = build_sprite_basic_loader(manifest, sprite_files)
        basic_path = os.path.join(output_dir, "sprites.bas")
        _write_text(basic_path, basic_content)

    result_payload = {
        "files": {
            "sprites": sprite_files,
            "positions": positions_path,
            "manifest": manifest_path,
        },
        "metadata": sprite_meta,
    }
    if asm_path:
        result_payload["files"]["asm_include"] = asm_path
    if basic_path:
        result_payload["files"]["basic_loader"] = basic_path
    return result_payload
