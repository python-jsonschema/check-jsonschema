"""
A file-like object specifically for use within check-jsonschema.

Inspired heavily by `click`'s internal `LazyFile` object.

Features:

- fixed mode ("rb")
- a "check_can_open()" function which will try to open and close the file, but only
  if it looks like a regular file
- passthrough of most attributes to the underlying file object
- automatically grabs binary stdin when the input name is "-"
- `close()` does nothing on stdin
"""

import os
import stat
import sys
import types
import typing as t

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class BinaryFileInput:
    def __init__(self, name: str) -> None:
        self.name = name

        self._stream: t.BinaryIO | None = None
        self._is_stdin: bool = False
        if self.name == "-":
            self._stream = sys.stdin.buffer
            self._is_stdin = True

    def check_can_open(self) -> None:
        if self._is_stdin:
            return

        if not stat.S_ISFIFO(os.stat(self.name).st_mode):
            # Open and close the file in case we're opening it for
            # reading so that we can catch at least some errors in
            # some cases early.
            self._open_handle.close()
            self._stream = None

    @property
    def _open_handle(self) -> t.BinaryIO:
        if self._stream is None:
            self._stream = open(self.name, "rb")
        return self._stream

    def close(self) -> None:
        if self._is_stdin:
            return
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self._open_handle, name)

    def __repr__(self) -> str:
        return "BinaryFileInput(filename={self.filename!r})"

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        self.close()

    def __iter__(self) -> t.Iterator[bytes]:
        return iter(self._open_handle)
