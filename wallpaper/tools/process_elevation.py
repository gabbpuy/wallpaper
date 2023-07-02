# -*- coding: utf-8 -*-
import os
import sys
import win32api

ElevatedArg = "_OK_"


def _elevate_self():
    """
    Gain (prompt) for Administrator privileges
    """
    if hasattr(sys, "frozen"):
        args = ['"{0}"'.format(a) for a in sys.argv[1:]]
    else:
        args = ['"{0}"'.format(a) for a in sys.argv]

    args.append(ElevatedArg)

    win32api.ShellExecute(0,
                          "runas",
                          sys.executable,
                          ' '.join(args),
                          os.getcwd(),
                          0
    )


def elevate_self():
    if ElevatedArg not in sys.argv:
        _elevate_self()
        sys.exit(1)
