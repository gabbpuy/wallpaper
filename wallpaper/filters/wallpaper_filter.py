# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABCMeta, abstractmethod
import logging

from PIL import Image

from wallpaper.geom.point import Point

logger = logging.getLogger(__name__)


class WallpaperFilter(metaclass=ABCMeta):
    """
    Base class for image filter. This can be a small image or the entire desktop

    Subclassers should override the protected `_filter` method
    """
    Filters = {}

    @staticmethod
    def register(cls):
        try:
            WallpaperFilter.Filters[cls.__name__.lower()] = cls()
        except:
            logger.exception('Cannot register filter %s', cls)

    @staticmethod
    def list_filters():
        return list(WallpaperFilter.Filters.keys())

    @staticmethod
    def get_filter(filter_name: str) -> WallpaperFilter | DummyFilter:
        return WallpaperFilter.Filters.get(filter_name, DummyFilter())

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        WallpaperFilter.register(cls)

    def __call__(self, image: Image.Image, monitor: 'Monitor' | None = None, position: Point | tuple | None = None) -> Image.Image:
        """
        Express the filter

        :param image: PIL Image
        :param monitor: The Monitor being rendered to
        :param position: The position of the image
        :return: PIL Image
        """
        try:
            return self._filter(image, monitor, position)
        except:
            logger.exception('Could not filter image %s', self.__class__.__name__)
            return image

    @abstractmethod
    def _filter(self, image: Image.Image, monitor: 'Monitor', position: Point) -> Image.Image:
        """
        Override this method to implement the filter
        :param image: PIL Image
        :param monitor: The monitor being rendered to
        :param position: The position on the desktop (TL) of the image
        :return: PIL Image
        """
        return image

    @staticmethod
    def _shrink_rect(rect: tuple, d: int = 1) -> tuple[tuple[int, int], tuple[int, int]]:
        (x, y), (w, h) = rect
        return (x + d, y + d), (w - d, h - d)


class DummyFilter:
    def __call__(self, image: Image.Image, monitor: 'Monitor', position: Point) -> Image.Image:
        return image
