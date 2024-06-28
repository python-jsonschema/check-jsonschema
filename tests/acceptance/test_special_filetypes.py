import multiprocessing
import os
import platform
import sys

import pytest
import responses


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


# helper (in global scope) for multiprocessing "spawn" to be able to use to launch
# background writers
def _fifo_write(path, data):
    fd = os.open(path, os.O_WRONLY)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


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

    spawn_ctx = multiprocessing.get_context("spawn")

    schema_proc = spawn_ctx.Process(
        target=_fifo_write, args=(schema_path, b'{"type": "integer"}')
    )
    schema_proc.start()
    instance_data = b"42" if check_succeeds else b'"foo"'
    instance_proc = spawn_ctx.Process(
        target=_fifo_write, args=(instance_path, instance_data)
    )
    instance_proc.start()

    try:
        result = run_line(
            ["check-jsonschema", "--schemafile", str(schema_path), str(instance_path)]
        )
        if check_succeeds:
            assert result.exit_code == 0
        else:
            assert result.exit_code == 1
    finally:
        schema_proc.terminate()
        instance_proc.terminate()


@pytest.mark.parametrize("check_passes", (True, False))
def test_remote_schema_requiring_retry(run_line, check_passes, tmp_path):
    """
    a "remote schema" (meaning HTTPS) with bad data, therefore requiring that a retry
    fires in order to parse
    """
    schema_loc = "https://example.com/schema1.json"
    responses.add("GET", schema_loc, body="", match_querystring=None)
    responses.add(
        "GET",
        schema_loc,
        headers={"Last-Modified": "Sun, 01 Jan 2000 00:00:01 GMT"},
        json={"type": "integer"},
        match_querystring=None,
    )

    instance_path = tmp_path / "instance.json"
    instance_path.write_text("42" if check_passes else '"foo"')

    result = run_line(
        ["check-jsonschema", "--schemafile", schema_loc, str(instance_path)]
    )
    if check_passes:
        assert result.exit_code == 0
    else:
        assert result.exit_code == 1


@pytest.mark.parametrize("check_passes", (True, False))
@pytest.mark.parametrize("using_stdin", ("schema", "instance"))
def test_schema_or_instance_from_stdin(
    run_line, check_passes, tmp_path, monkeypatch, using_stdin
):
    """
    a "remote schema" (meaning HTTPS) with bad data, therefore requiring that a retry
    fires in order to parse
    """
    if using_stdin == "schema":
        instance_path = tmp_path / "instance.json"
        instance_path.write_text("42" if check_passes else '"foo"')

        result = run_line(
            ["check-jsonschema", "--schemafile", "-", str(instance_path)],
            input='{"type": "integer"}',
        )
    elif using_stdin == "instance":
        schema_path = tmp_path / "schema.json"
        schema_path.write_text('{"type": "integer"}')
        instance = "42" if check_passes else '"foo"'

        result = run_line(
            ["check-jsonschema", "--schemafile", schema_path, "-"],
            input=instance,
        )
    else:
        raise NotImplementedError
    if check_passes:
        assert result.exit_code == 0
    else:
        assert result.exit_code == 1
