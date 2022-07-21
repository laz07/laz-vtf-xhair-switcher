# -*- coding: utf-8 -*-

from .rgba8888 import RGBA8888


class ARGB8888(RGBA8888):
    id = 11

    @staticmethod
    def _sort_pixel_rgba(pixel):
        return [pixel[1], pixel[2], pixel[3], pixel[0]]
