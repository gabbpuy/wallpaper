# -*- coding: utf-8 -*-
from .monitor import Monitor


def get_monitors(size):
    return Monitor("Generic", size, size, 1, 0),
