"""cPanel/Passenger entry point for Django.

This file is used by Phusion Passenger in cPanel deployments.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force production settings unless cPanel defines a different settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject.settings.production')

from DjangoProject.wsgi import application  # noqa: E402
