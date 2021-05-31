# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class Size:
    width: int
    height: int

    def __repr__(self):
        return f'<Size ({self.width}, {self.height})>'

    def __iter__(self):
        yield self.width
        yield self.height
