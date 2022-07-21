# -*- coding: utf-8 -*-
from typing import Type

from .abstract_format import AbstractFormat
from .abgr8888 import ABGR8888
from .argb8888 import ARGB8888
from .bgr888 import BGR888
from .bgra8888 import BGRA8888
from .dxt1 import DXT1
from .dxt5 import DXT5
from .rgb888 import RGB888
from .rgba8888 import RGBA8888

available_formats = [ABGR8888, ARGB8888, BGR888, BGRA8888, DXT1, DXT5, RGB888, RGBA8888]


def get_parser(image_format: int) -> Type[AbstractFormat]:
    for parser in available_formats:
        if image_format == parser.id:
            return parser

    raise TypeError(f"Unknown image format {image_format}")


__all__ = ["AbstractFormat", "get_parser"]
