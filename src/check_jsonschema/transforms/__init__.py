from __future__ import annotations

import typing as t

from .azure_pipelines import azure_main
from .gitlab import gitlab_init

DataT = t.Union[dict, list]


class Transform:
    def __init__(
        self,
        *,
        on_init: t.Callable[[], None] | None = None,
        on_data: t.Callable[[DataT], DataT] | None = None,
    ):
        self.on_init = on_init
        self.on_data = on_data


TRANSFORM_LIBRARY: dict[str, t.Callable[[dict | list], dict | list]] = {
    "azure-pipelines": Transform(on_data=azure_main),
    "gitlab-ci": Transform(on_init=gitlab_init),
}

__all__ = ("TRANSFORM_LIBRARY",)
