# -*- coding: utf-8 -*-
import copy
import itertools

from .point import Point
from .size import Size


class Rect:
    __slots__ = ('top_left', 'size', 'bottom_right')

    def __init__(self, top_left: Point, size: Size):
        self.top_left = top_left
        self.size = size
        self.bottom_right = Point(top_left.x + size.width,
                                  top_left.y + size.height)

    def copy(self):
        return Rect(copy.copy(self.top_left), copy.copy(self.size))

    def intersection(self, other):
        a, b = self, other
        x1 = max(min(a.left, a.right), min(b.left, b.right))
        y1 = max(min(a.top, a.bottom), min(b.top, b.bottom))
        x2 = min(max(a.left, a.right), max(b.left, b.right))
        y2 = min(max(a.top, a.bottom), max(b.top, b.bottom))
        if x1 < x2 and y1 < y2:
            return type(self)(Point(x1, y1), Size(x2 - x1, y2 - y1))

    __and__ = intersection

    def difference(self, other):
        inter = self & other
        if not inter:
            yield self
            return
        xs = {self.left, self.right}
        ys = {self.top, self.bottom}
        if self.left < other.left < self.right:
            xs.add(other.left)
        if self.left < other.right < self.right:
            xs.add(other.right)
        if self.top < other.top < self.bottom:
            ys.add(other.top)
        if self.top < other.bottom < self.bottom:
            ys.add(other.bottom)
        for (x1, x2), (y1, y2) in itertools.product(
                pairwise(sorted(xs)), pairwise(sorted(ys))
        ):
            rect = type(self)(Point(x1, y1), Size(x2 - x1, y2 - y1))
            if rect != inter:
                yield rect

    def __sub__(self, other):
        return list(self.difference(other))

    def __iter__(self):
        yield self.left
        yield self.top
        yield self.right
        yield self.bottom

    def __eq__(self, other):
        return isinstance(other, Rect) and tuple(self) == tuple(other)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return 'Rect: ({}, {}, {}, {})'.format(self.left, self.top, self.right, self.bottom)

    def __lt__(self, other: 'Rect'):
        """
        We keep a priority queue of rects for some things but if two areas are equal we need a comparison for
        rectangles. Order by distance to (0, 0) it's as good as any.
        :param other:
        :return:
        """
        origin = Point(0, 0)
        return self.distance(self.top_left, origin) < self.distance(other.top_left, origin)

    @staticmethod
    def distance(p1: Point, p2: Point):
        x2 = (p1.x - p2.x) ** 2
        y2 = (p1.y - p2.y) ** 2
        return (x2 + y2) ** .5

    @property
    def left(self):
        return self.top_left.x

    @property
    def top(self):
        return self.top_left.y

    @property
    def w(self):
        return self.size.width

    @property
    def h(self):
        return self.size.height

    @property
    def right(self):
        return self.bottom_right.x

    @property
    def bottom(self):
        return self.bottom_right.y

    @property
    def area(self):
        return self.w * self.h


def pairwise(iterable):
    # //docs.python.org/dev/library/itertools.html#recipes
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)
