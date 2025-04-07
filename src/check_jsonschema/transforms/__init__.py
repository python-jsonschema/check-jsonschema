from __future__ import annotations

import typing

from .azure_pipelines import AZURE_TRANSFORM
from .gitlab import GITLAB_TRANSFORM

if typing.TYPE_CHECKING:
    from .base import Transform

TRANSFORM_LIBRARY: dict[str, Transform] = {
    "azure-pipelines": AZURE_TRANSFORM,
    "gitlab-ci": GITLAB_TRANSFORM,
}

__all__ = ("TRANSFORM_LIBRARY",)
