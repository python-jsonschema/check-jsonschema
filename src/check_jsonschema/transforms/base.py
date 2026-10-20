from __future__ import annotations

import typing as t

import ruamel.yaml

_AnyData: t.TypeAlias = list[t.Any] | dict[t.Any, t.Any]


class Transform:
    def __init__(
        self,
        *,
        on_data: t.Callable[[_AnyData], _AnyData] | None = None,
    ) -> None:
        self.on_data = on_data

    def modify_yaml_implementation(self, implementation: ruamel.yaml.YAML) -> None:
        pass

    def __call__(self, data: _AnyData) -> _AnyData:
        if self.on_data is not None:
            return self.on_data(data)
        return data
