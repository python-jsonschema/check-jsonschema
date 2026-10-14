from __future__ import annotations

import codecs
import io
import re
import typing as t
import warnings

import ruamel.yaml

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


def _has_yaml_11_directive(data: bytes) -> bool:
    """Look for an explicit YAML 1.1 directive in the document preamble."""
    encoding = (
        "utf-16"
        if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE))
        else "utf-8-sig"
    )
    try:
        with io.TextIOWrapper(io.BytesIO(data), encoding=encoding) as stream:
            for line in stream:
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if not line.startswith("%"):
                    break
                directive = line.split("#", 1)[0].split()
                if directive[0] == "%YAML":
                    return len(directive) == 2 and bool(
                        re.fullmatch(r"0*1\.0*1", directive[1])
                    )
    except UnicodeError:
        # Let the YAML implementation report invalid input encodings.
        pass
    return False


def impl2loader(
    primary: ruamel.yaml.YAML, *fallbacks: ruamel.yaml.YAML
) -> t.Callable[[t.IO[bytes]], t.Any]:
    def load(stream: t.IO[bytes]) -> t.Any:
        stream_bytes = stream.read()
        lasterr: ruamel.yaml.YAMLError | None = None
        data: t.Any = _data_sentinel
        implementations = [primary] + list(fallbacks)
        if _has_yaml_11_directive(stream_bytes):
            # The C parser can accept YAML 1.1 while applying YAML 1.2 rules.
            implementations.sort(key=lambda impl: not impl.pure)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ruamel.yaml.error.ReusedAnchorWarning)
            for impl in implementations:
                try:
                    data = impl.load(stream_bytes)
                except ruamel.yaml.YAMLError as e:
                    lasterr = e
                else:
                    break
        if data is _data_sentinel and lasterr is not None:
            raise lasterr
        return _normalize(data)

    return load
