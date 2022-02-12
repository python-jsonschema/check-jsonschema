import linecache
import sys
import traceback
import typing as t

import jsonschema

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


def print_shortened_error(
    err: Exception, *, stream: t.TextIO = sys.stderr, indent: int = 0
) -> None:
    print(indent * " " + f"{type(err).__name__}: {err}", file=stream)
    lineno = err.__traceback__.tb_lineno
    tb_frame = err.__traceback__.tb_frame
    filename = tb_frame.f_code.co_filename
    line = linecache.getline(filename, lineno)
    print((indent + 2) * " " + f'in "{filename}", line {lineno}', file=stream)
    print((indent + 2) * " " + ">>> " + line.strip(), file=stream)


def print_shortened_trace(
    caught_err: Exception, *, stream: t.TextIO = sys.stderr
) -> None:
    err_stack = [caught_err]
    while err_stack[-1].__context__ is not None:
        err_stack.append(err_stack[-1].__context__)
    print_shortened_error(caught_err, stream=stream)
    indent = 0
    for err in err_stack[1:]:
        indent += 2
        print("\n" + indent * " " + "caused by\n", file=stream)
        print_shortened_error(err, stream=stream, indent=indent)


def print_error(err: Exception, mode: str = "short"):
    if mode == "short":
        print_shortened_trace(err)
    else:
        traceback.print_exception(type(err), err, err.__traceback__)


def json_path(err: jsonschema.ValidationError) -> str:
    """
    This method is a backport of the json_path attribute provided by
    jsonschema.ValidationError for jsonschema v4.x

    It is needed until python3.6 is no longer supported by check-jsonschema,
    as jsonschema 4 dropped support for py36
    """
    path = "$"
    for elem in err.absolute_path:
        if isinstance(elem, int):
            path += "[" + str(elem) + "]"
        else:
            path += "." + elem
    return path


def format_validation_error_message(err, filename=None):
    if filename:
        return f"\033[0;33m{filename}::{json_path(err)}: \033[0m{err.message}"
    return f"  \033[0;33m{json_path(err)}: \033[0m{err.message}"


def iter_validation_error(err):
    for e in err.context:
        yield e
        yield from iter_validation_error(e)


def print_validation_error(
    filename: str, err: jsonschema.ValidationError, show_all_errors: bool = False
):
    def _echo(s):
        print("  " + s, file=sys.stderr)

    _echo(format_validation_error_message(err, filename=filename))
    if err.context and show_all_errors:
        best_match = jsonschema.exceptions.best_match(err.context)
        _echo("Underlying errors caused this.")
        _echo("Best Match:")
        _echo(format_validation_error_message(best_match))
        _echo("All Errors:")
        for err in iter_validation_error(err):
            _echo(format_validation_error_message(err))
