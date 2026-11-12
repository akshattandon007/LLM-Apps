"""Allow running as `python -m isbnscan`."""
import sys
from .cli import main

sys.exit(main())
