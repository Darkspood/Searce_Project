"""Makes the app modules (dishes, context_engine, matching_engine, charts, app)
importable as top-level modules regardless of where pytest is invoked from."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
