from __future__ import annotations

import typing

from .azure_pipelines import AZURE_TRANSFORM
from .base import Transform  # noqa: TCH001
from .gitlab import GITLAB_TRANSFORM

TRANSFORM_LIBRARY: dict[str, Transform] = {
    "azure-pipelines": AZURE_TRANSFORM,
    "gitlab-ci": GITLAB_TRANSFORM,
}

__all__ = ("TRANSFORM_LIBRARY",)
