"""Allow ``python -m qrcraft`` to invoke the CLI."""

import sys
from qrcraft.cli import main

sys.exit(main())