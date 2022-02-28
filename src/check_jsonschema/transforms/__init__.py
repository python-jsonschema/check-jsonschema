from __future__ import annotations

import typing as t

from .azure_pipelines import azure_main

TRANFORM_LIBRARY: dict[str, t.Callable[[dict | list], dict | list]] = {
    "azure-pipelines": azure_main,
}

__all__ = ("TRANSFORM_LIBRARY",)
