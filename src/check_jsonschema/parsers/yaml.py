from __future__ import annotations

import typing as t
import warnings

import ruamel.yaml

from .metadata import MultiDocumentData, ParsedDocument

ParseError = ruamel.yaml.YAMLError


def construct_yaml_implementation(
    typ: str = "safe", pure: bool = False
) -> ruamel.yaml.YAML:
    implementation = ruamel.yaml.YAML(typ=typ, pure=pure)

    # workaround global state
    # see: https://sourceforge.net/p/ruamel-yaml/tickets/341/
    class GeneratedSafeConstructor(ruamel.yaml.SafeConstructor):
        pass

    implementation.Constructor = GeneratedSafeConstructor

    # ruamel.yaml parses timestamp values into datetime.datetime values
    # however, JSON does not support native datetimes, so JSON Schema formats for
    # dates apply to strings
    # Turn off this feature, instructing the parser to load datetimes as strings
    implementation.constructor.yaml_constructors["tag:yaml.org,2002:timestamp"] = (
        implementation.constructor.yaml_constructors["tag:yaml.org,2002:str"]
    )

    return implementation


def _normalize(data: t.Any) -> t.Any:
    """
    Normalize YAML data to fit the requirements to be JSON-encodeable.

    Currently this applies the following transformation:
        dict keys are converted to strings

    Additional tweaks can be added in this layer in the future if necessary.
    """
    if isinstance(data, dict):
        return {str(k): _normalize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_normalize(x) for x in data]
    else:
        return data


_data_sentinel = object()


def _is_multidoc_error(err: ruamel.yaml.YAMLError) -> bool:
    return isinstance(err, ruamel.yaml.composer.ComposerError) and (
        "expected a single document in the stream" in str(err)
    )


def _document_start_lines(
    implementation: ruamel.yaml.YAML, stream_bytes: bytes, num_docs: int
) -> tuple[int | None, ...]:
    try:
        nodes = list(implementation.compose_all(stream_bytes))
    except ruamel.yaml.YAMLError:
        return (None,) * num_docs
    return tuple(
        node.start_mark.line + 1 if node.start_mark is not None else None
        for node in nodes
    )


def _load_all_documents(
    implementation: ruamel.yaml.YAML, stream_bytes: bytes
) -> MultiDocumentData:
    documents = list(implementation.load_all(stream_bytes))
    lines = _document_start_lines(implementation, stream_bytes, len(documents))
    return MultiDocumentData(
        tuple(
            ParsedDocument(data=_normalize(doc), line=line)
            for doc, line in zip(documents, lines)
        )
    )


def impl2loader(
    primary: ruamel.yaml.YAML, *fallbacks: ruamel.yaml.YAML
) -> t.Callable[[t.IO[bytes]], t.Any]:
    def load(stream: t.IO[bytes]) -> t.Any:
        stream_bytes = stream.read()
        lasterr: ruamel.yaml.YAMLError | None = None
        data: t.Any = _data_sentinel
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ruamel.yaml.error.ReusedAnchorWarning)
            for impl in [primary] + list(fallbacks):
                try:
                    data = impl.load(stream_bytes)
                except ruamel.yaml.YAMLError as err:
                    if _is_multidoc_error(err):
                        try:
                            data = _load_all_documents(impl, stream_bytes)
                        except ruamel.yaml.YAMLError as multidoc_err:
                            lasterr = multidoc_err
                            continue
                        else:
                            break
                    lasterr = err
                else:
                    break
        if data is _data_sentinel and lasterr is not None:
            raise lasterr
        if isinstance(data, MultiDocumentData):
            return data
        return _normalize(data)

    return load
