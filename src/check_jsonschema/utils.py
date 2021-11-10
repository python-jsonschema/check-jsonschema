import linecache
import sys
import traceback
import typing as t

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
