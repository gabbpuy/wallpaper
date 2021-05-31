# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int

    def __repr__(self):
        return f'<Point ({self.x}, {self.y})>'

    def __iter__(self):
        yield self.x
        yield self.y

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
