import os
import platform
import sys

import pytest

from check_jsonschema.utils import filename2path


@pytest.mark.skipif(
    not (platform.system() == "Linux"), reason="test requires /proc/self/ mechanism"
)
@pytest.mark.skipif(sys.version_info < (3, 8), reason="test uses os.memfd_create")
@pytest.mark.parametrize("use_pid_in_path", (True, False))
def test_filename2path_on_memfd(use_pid_in_path):
    """
    create a memory file descriptor with a path in /proc/self/fd/
    and then attempt to resolve that to an absolute Path object
    the end result should be untouched

    pathlib behavior is, for example,

    >>> pathlib.Path("/proc/self/fd/4").resolve()
    PosixPath('/memfd:myfd (deleted)')
    """
    testfd = os.memfd_create("test_filename2path")
    try:
        pid = os.getpid() if use_pid_in_path else "self"
        filename = f"/proc/{pid}/fd/{testfd}"
        path = filename2path(filename)

        assert str(path) == filename
    finally:
        os.close(testfd)
