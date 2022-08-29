from __future__ import annotations

import linecache
import os
import pathlib
import traceback
import typing as t
import urllib.parse
import urllib.request

import click
import jsonschema

WINDOWS = os.name == "nt"


# this is a short list of schemes which will be recognized as being
# schemes at all; anything else will not even be reported as an
# unsupported scheme
KNOWN_URL_SCHEMES = [
    "",
    "ftp",
    "gopher",
    "http",
    "file",
    "https",
    "shttp",
    "rsync",
    "svn",
    "svn+ssh",
    "sftp",
    "nfs",
    "git",
    "git+ssh",
    "ws",
    "wss",
]


def is_url_ish(path: str) -> bool:
    r"""
    Returns true if the input path looks like a URL.

    NB: This needs to be done carefully to avoid mishandling of Windows paths
    starting with 'C:\' (and so forth) as URLs. urlparse from urllib will treat
    'C' as a scheme if asked to parse a Windows path.
    """
    if ":" not in path:
        return False
    scheme = path.split(":", 1)[0].lower()
    return scheme in KNOWN_URL_SCHEMES


def filename2path(filename: str) -> pathlib.Path:
    """
    Convert a filename which may be a local file URI to a pathlib.Path object

    This implementation was influenced strongly by how pip handles this problem:
      https://github.com/pypa/pip/blob/bf91a079791f2daf4339115fb39ce7d7e33a9312/src/pip/_internal/utils/urls.py#L26
    """
    if not filename.startswith("file://"):
        # for local paths, support use of `~`
        p = pathlib.Path(filename).expanduser()
    else:
        urlinfo = urllib.parse.urlsplit(filename)
        # local (vs UNC paths)
        is_local_path = urlinfo.netloc in (None, "", "localhost")

        if is_local_path:
            netloc = ""
        elif WINDOWS:
            netloc = "\\\\" + urlinfo.netloc

        filename = urllib.request.url2pathname(netloc + urlinfo.path)

        # url2pathname on windows local paths can produce paths like
        #   /C:/Users/foo/...
        # the leading slash messes up a lot of logic for pathlib and similar functions
        # so strip the leading slash in this case
        if WINDOWS and is_local_path and filename.startswith("/"):
            filename = filename[1:]

        p = pathlib.Path(filename)

    return p.resolve()


def format_shortened_error(err: Exception, *, indent: int = 0) -> str:
    lines = []
    lines.append(indent * " " + f"{type(err).__name__}: {err}")
    if err.__traceback__ is not None:
        lineno = err.__traceback__.tb_lineno
        tb_frame = err.__traceback__.tb_frame
        filename = tb_frame.f_code.co_filename
        line = linecache.getline(filename, lineno)
        lines.append((indent + 2) * " " + f'in "{filename}", line {lineno}')
        lines.append((indent + 2) * " " + ">>> " + line.strip())
    return "\n".join(lines)


def format_shortened_trace(caught_err: Exception) -> str:
    err_stack: list[Exception] = [caught_err]
    while err_stack[-1].__context__ is not None:
        err_stack.append(err_stack[-1].__context__)  # type: ignore[arg-type]

    parts = [format_shortened_error(caught_err)]
    indent = 0
    for err in err_stack[1:]:
        indent += 2
        parts.append("\n" + indent * " " + "caused by\n")
        parts.append(format_shortened_error(err, indent=indent))
    return "\n".join(parts)


def format_error(err: Exception, mode: str = "short") -> str:
    if mode == "short":
        return format_shortened_trace(err)
    else:
        return "".join(traceback.format_exception(type(err), err, err.__traceback__))


def print_error(err: Exception, mode: str = "short") -> None:
    click.echo(format_error(err, mode=mode), err=True)


def iter_validation_error(
    err: jsonschema.ValidationError,
) -> t.Iterator[jsonschema.ValidationError]:
    if err.context:
        for e in err.context:
            yield e
            yield from iter_validation_error(e)
