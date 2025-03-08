# -*- coding: utf-8 -*-
from typing import Sequence
from .monitor import Monitor


def get_monitors(size) -> Sequence[Monitor]:
    return Monitor("Generic", size, size, 1, 0),
