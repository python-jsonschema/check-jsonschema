import pytest

from check_jsonschema import main


class _CLIResult:
    def __init__(self):
        self.err = None
        self.exit_code = 0
        self.stdout = ""
        self.stderr = ""


@pytest.fixture
def cli_runner(capsys):
    def func(args, *, expect_ok=True):
        res = _CLIResult()

        try:
            main(args)
        except SystemExit as err:
            res.exit_code = err.code
            res.err = err
        except Exception as err:
            res.exit_code = 1
            res.err = err

        captured = capsys.readouterr()
        res.stdout = captured.out
        res.stderr = captured.err

        if expect_ok:
            assert res.exit_code == 0

        return res

    return func
