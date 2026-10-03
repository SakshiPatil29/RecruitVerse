"""
Process-startup fixes that must run before anything else is imported.

Currently one thing: torch import ordering.

On Windows, importing pandas before torch leaves the process in a state
where torch's native libraries fail to initialise:

    OSError: [WinError 1114] A dynamic link library (DLL) initialization
    routine failed. Error loading ...\\torch\\lib\\c10.dll

Reproduce with `python -c "import pandas, torch"` (fails) versus
`python -c "import torch, pandas"` (works). KMP_DUPLICATE_LIB_OK makes no
difference, so this is a DLL conflict rather than the usual duplicated
OpenMP runtime. Importing torch first is the reliable fix.

This matters because src/ui/pages/* import pandas at module load, so by
the time the recruiter presses "Rank candidates" — the first thing that
pulls in sentence-transformers, and therefore torch — the process is
already poisoned and semantic scoring falls back to lexical similarity on
every run. Calling preload_torch() at the top of app.py, before any page
module is imported, keeps real embeddings available.

Costs ~2.5s at startup. If torch isn't installed at all, this is a no-op
and embedding_matcher's lexical fallback takes over.
"""

import logging

logger = logging.getLogger(__name__)


def preload_torch():
    """Import torch before pandas. Returns True if torch is now usable."""
    try:
        import torch  # noqa: F401
    except ImportError:
        # sentence-transformers isn't installed; the lexical fallback in
        # src/matching/embedding_matcher.py handles this.
        return False
    except Exception as exc:
        logger.warning("torch failed to load (%s); semantic scoring will use "
                       "the lexical fallback.", exc)
        return False
    return True
