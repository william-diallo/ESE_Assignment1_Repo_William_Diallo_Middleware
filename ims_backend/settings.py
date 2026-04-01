"""Environment-aware Django settings entrypoint."""

import os
import sys

environment = os.getenv("DJANGO_ENV", "dev").lower()
if "test" in sys.argv:
    environment = "test"

if environment == "test":
    from .settings_test import *  # noqa: F401,F403
elif environment == "prod":
    from .settings_prod import *  # noqa: F401,F403
else:
    from .settings_dev import *  # noqa: F401,F403
