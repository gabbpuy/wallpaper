# -*- coding: utf-8 -*-

import platform
this_platform = platform.platform().lower()

if this_platform.startswith('windows'):
    from .windows import get_monitors
elif this_platform.startswith('macos'):
    from .osx import get_monitors
else:
    from .generic import get_monitors

from .monitor import Monitor
