"""CLI for C64 graphics conversions."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .converter import analyze_image, convert_bitmap, convert_sprites


def _parse_addresses(value: Optional[str]) -> Optional[Dict[str, int]]:
    if not value:
        return None
    parsed = json.loads(value)
    return {k: int(v, 0) if isinstance(v, str) else int(v) for k, v in parsed.items()}


def _parse_regions(value: Optional[str]) -> Optional[List[Dict[str, int]]]:
    if not value:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("regions must be a JSON list")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="C64 graphics conversion tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_bitmap_parser = subparsers.add_parser("convert-bitmap", help="Convert image to bitmap assets")
    convert_bitmap_parser.add_argument("input_path")
    convert_bitmap_parser.add_argument("output_dir")
    convert_bitmap_parser.add_argument("--mode", default="bitmap_multicolor", choices=["bitmap_hires", "bitmap_multicolor"])
    convert_bitmap_parser.add_argument("--addresses", help="JSON map of addresses (hex or int)")
    convert_bitmap_parser.add_argument("--dither", action="store_true")
    convert_bitmap_parser.add_argument("--background-color", type=int)
    convert_bitmap_parser.add_argument("--border-color", type=int)
    convert_bitmap_parser.add_argument("--strict", action="store_true")
    convert_bitmap_parser.add_argument("--emit-asm", action="store_true")
    convert_bitmap_parser.add_argument("--emit-basic", action="store_true")

    convert_sprites_parser = subparsers.add_parser("convert-sprites", help="Convert image to sprite assets")
    convert_sprites_parser.add_argument("input_path")
    convert_sprites_parser.add_argument("output_dir")
    convert_sprites_parser.add_argument("--sprite-mode", default="hires", choices=["hires", "multicolor"])
    convert_sprites_parser.add_argument("--regions", help="JSON list of crop regions")
    convert_sprites_parser.add_argument("--background-color", type=int)
    convert_sprites_parser.add_argument("--dither", action="store_true")
    convert_sprites_parser.add_argument("--strict", action="store_true")
    convert_sprites_parser.add_argument("--emit-asm", action="store_true")
    convert_sprites_parser.add_argument("--emit-basic", action="store_true")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze image constraints")
    analyze_parser.add_argument("input_path")
    analyze_parser.add_argument("--mode", default="bitmap_multicolor", choices=["bitmap_hires", "bitmap_multicolor"])
    analyze_parser.add_argument("--constraints-only", action="store_true")
    analyze_parser.add_argument("--background-color", type=int)
    analyze_parser.add_argument("--dither", action="store_true")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "convert-bitmap":
        result = convert_bitmap(
            input_path=args.input_path,
            mode=args.mode,
            output_dir=args.output_dir,
            addresses=_parse_addresses(args.addresses),
            dither=args.dither,
            background_color=args.background_color,
            border_color=args.border_color,
            strict=args.strict,
            emit_asm=args.emit_asm,
            emit_basic=args.emit_basic,
        )
    elif args.command == "convert-sprites":
        result = convert_sprites(
            input_path=args.input_path,
            sprite_mode=args.sprite_mode,
            output_dir=args.output_dir,
            regions=_parse_regions(args.regions),
            background_color=args.background_color,
            dither=args.dither,
            strict=args.strict,
            emit_asm=args.emit_asm,
            emit_basic=args.emit_basic,
        )
    else:
        result = analyze_image(
            input_path=args.input_path,
            mode=args.mode,
            constraints_only=args.constraints_only,
            background_color=args.background_color,
            dither=args.dither,
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
