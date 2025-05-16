import os
import platform

import pytest

from check_jsonschema.cli.main_command import build_checker
from check_jsonschema.cli.main_command import main as cli_main


@pytest.mark.skipif(
    platform.system() != "Linux", reason="test requires /proc/self/ mechanism"
)
def test_open_file_usage_never_exceeds_1000(cli_runner, monkeypatch, tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text("{}")

    args = [
        "--schemafile",
        str(schema_path),
    ]

    for i in range(2000):
        instance_path = tmp_path / f"file{i}.json"
        instance_path.write_text("{}")
        args.append(str(instance_path))

    checker = None

    def fake_execute(argv):
        nonlocal checker
        checker = build_checker(argv)

    monkeypatch.setattr("check_jsonschema.cli.main_command.execute", fake_execute)
    res = cli_runner.invoke(cli_main, args)
    assert res.exit_code == 0, res.stderr

    assert checker is not None
    assert len(os.listdir("/proc/self/fd")) < 2000
    for _fname, _data in checker._instance_loader.iter_files():
        assert len(os.listdir("/proc/self/fd")), 2000
