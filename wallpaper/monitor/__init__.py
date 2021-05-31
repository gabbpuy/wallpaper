# -*- coding: utf-8 -*-

import platform
this_platform = platform.platform()

if this_platform.startswith('Windows'):
    from .windows import get_monitors
else:
    from .generic import get_monitors

from .monitor import Monitor
