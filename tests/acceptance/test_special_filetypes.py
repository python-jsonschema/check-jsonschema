import os
import platform
import sys
import threading

import pytest


@pytest.mark.skipif(
    platform.system() != "Linux", reason="test requires /proc/self/ mechanism"
)
@pytest.mark.skipif(sys.version_info < (3, 8), reason="test uses os.memfd_create")
def test_schema_and_instance_in_memfds(run_line_simple):
    """
    create memory file descriptors and write schema and instance data into those
    ensure the result works when the paths to those fds are passed on the CLI
    """
    schemafd = os.memfd_create("test_memfd_schema")
    instancefd = os.memfd_create("test_memfd_instance")
    try:
        os.write(schemafd, b'{"type": "integer"}')
        os.write(instancefd, b"42")

        schema_path = f"/proc/self/fd/{schemafd}"
        instance_path = f"/proc/self/fd/{instancefd}"

        run_line_simple(["--schemafile", schema_path, instance_path])
    finally:
        os.close(schemafd)
        os.close(instancefd)


@pytest.mark.skipif(os.name != "posix", reason="test requires mkfifo")
@pytest.mark.parametrize("check_succeeds", (True, False))
def test_schema_and_instance_in_fifos(tmp_path, run_line, check_succeeds):
    """
    create fifos and write schema and instance data into those
    ensure the result works when the paths to those fds are passed on the CLI
    """
    schema_path = tmp_path / "schema"
    instance_path = tmp_path / "instance"
    os.mkfifo(schema_path)
    os.mkfifo(instance_path)

    # execute FIFO writes as blocking writes in background threads
    # nonblocking writes fail file existence if there's no reader, so using a FIFO
    # requires some level of concurrency
    def fifo_write(path, data):
        fd = os.open(path, os.O_WRONLY)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)

    schema_thread = threading.Thread(
        target=fifo_write, args=[schema_path, b'{"type": "integer"}']
    )
    schema_thread.start()
    instance_data = b"42" if check_succeeds else b'"foo"'
    instance_thread = threading.Thread(
        target=fifo_write, args=[instance_path, instance_data]
    )
    instance_thread.start()

    try:
        result = run_line(
            ["check-jsonschema", "--schemafile", str(schema_path), str(instance_path)]
        )
        if check_succeeds:
            assert result.exit_code == 0
        else:
            assert result.exit_code == 1
    finally:
        schema_thread.join(timeout=0.1)
        instance_thread.join(timeout=0.1)
