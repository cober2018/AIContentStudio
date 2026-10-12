"""Finite media geometry contract shared by stage routing and local providers."""

from __future__ import annotations

import math

ASPECT_RATIOS = {
    "1:1": (1, 1),
    "4:3": (4, 3),
    "3:4": (3, 4),
    "16:9": (16, 9),
    "9:16": (9, 16),
}


def canonical_aspect_ratio(value: object) -> str:
    if not isinstance(value, str) or value not in ASPECT_RATIOS:
        raise ValueError("aspect_ratio_unsupported")
    return value


def image_dimensions(pixels: int, aspect_ratio: str) -> tuple[int, int]:
    """Choose deterministic 8-pixel-aligned geometry under the pixel budget."""
    ratio_width, ratio_height = ASPECT_RATIOS[canonical_aspect_ratio(aspect_ratio)]
    if type(pixels) is not int or pixels < 512 * 512:
        raise ValueError("pixels_invalid")
    unit_limit = min(math.sqrt(pixels / (ratio_width * ratio_height)), 2048 / max(ratio_width, ratio_height))
    unit = math.floor(unit_limit / 8) * 8
    if unit < 8:
        raise ValueError("aspect_ratio_pixels_too_small")
    return unit * ratio_width, unit * ratio_height
