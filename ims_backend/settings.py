"""Environment-aware Django settings entrypoint."""

import os
import sys

environment = os.getenv("DJANGO_ENV", "dev").lower()
if "test" in sys.argv:
    environment = "test"

if environment == "test":
    from .settings_test import *
elif environment == "prod":
    from .settings_prod import *
else:
    from .settings_dev import *

