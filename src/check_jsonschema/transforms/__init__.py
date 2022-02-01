import typing as t

from .azure_pipelines import azure_main

DataT = t.Union[dict, list]
TransformT = t.Callable[[DataT], DataT]

TRANFORM_LIBRARY: t.Dict[str, TransformT] = {
    "azure-pipelines": azure_main,
}

__all__ = ("TRANSFORM_LIBRARY",)
