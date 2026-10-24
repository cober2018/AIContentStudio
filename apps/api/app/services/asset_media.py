"""Where the platform keeps its own media files on this Mac."""

import os
from pathlib import Path

_configured_media_root = os.environ.get("AI_STUDIO_MEDIA_ROOT")
if _configured_media_root and not Path(_configured_media_root).is_absolute():
    raise ValueError("AI_STUDIO_MEDIA_ROOT must be an absolute path")
if not _configured_media_root:
    from .storage_locations import configured_local_root

    _configured_media_root = configured_local_root()
MEDIA_ROOT = Path(_configured_media_root).resolve() if _configured_media_root else Path(__file__).resolve().parents[1] / "media"
