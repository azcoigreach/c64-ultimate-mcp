"""Shared constants for C64 graphics conversions."""

VIC_II_PALETTE = [
    {"index": 0, "name": "black", "rgb": (0, 0, 0), "hex": "#000000"},
    {"index": 1, "name": "white", "rgb": (255, 255, 255), "hex": "#ffffff"},
    {"index": 2, "name": "red", "rgb": (136, 0, 0), "hex": "#880000"},
    {"index": 3, "name": "cyan", "rgb": (170, 255, 238), "hex": "#aaffee"},
    {"index": 4, "name": "purple", "rgb": (204, 68, 204), "hex": "#cc44cc"},
    {"index": 5, "name": "green", "rgb": (0, 204, 85), "hex": "#00cc55"},
    {"index": 6, "name": "blue", "rgb": (0, 0, 170), "hex": "#0000aa"},
    {"index": 7, "name": "yellow", "rgb": (238, 238, 119), "hex": "#eeee77"},
    {"index": 8, "name": "orange", "rgb": (221, 136, 85), "hex": "#dd8855"},
    {"index": 9, "name": "brown", "rgb": (102, 68, 0), "hex": "#664400"},
    {"index": 10, "name": "light_red", "rgb": (255, 119, 119), "hex": "#ff7777"},
    {"index": 11, "name": "dark_gray", "rgb": (51, 51, 51), "hex": "#333333"},
    {"index": 12, "name": "gray", "rgb": (119, 119, 119), "hex": "#777777"},
    {"index": 13, "name": "light_green", "rgb": (170, 255, 102), "hex": "#aaff66"},
    {"index": 14, "name": "light_blue", "rgb": (0, 136, 255), "hex": "#0088ff"},
    {"index": 15, "name": "light_gray", "rgb": (187, 187, 187), "hex": "#bbbbbb"},
]

DEFAULT_ADDRESSES = {
    "bitmap": 0x2000,
    "screen": 0x0400,
    "color": 0xD800,
    "sprites": 0x3000,
}

BITMAP_MODES = {
    "bitmap_hires": {"width": 320, "height": 200},
    "bitmap_multicolor": {"width": 160, "height": 200},
}

SPRITE_MODES = {
    "hires": {"width": 24, "height": 21},
    "multicolor": {"width": 12, "height": 21},
}
