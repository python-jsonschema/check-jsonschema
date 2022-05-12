"""
Output formatters are called "reporters" because they take the result of validation
and report it back to the user.
"""

from __future__ import annotations

import abc
import json
import sys
import typing as t

import click
import jsonschema

from .utils import iter_validation_error


class Reporter(abc.ABC):
    @abc.abstractmethod
    def report_success(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def report_validation_errors(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
    ) -> None:
        raise NotImplementedError


class TextReporter(Reporter):
    def __init__(
        self,
        *,
        stream: t.TextIO | None = None,  # default stream is stdout (None)
        color: bool = True,
        verbosity: int = 0,
    ) -> None:
        self.stream = stream
        self.color = color
        self.verbosity = verbosity

    def echo(self, s: str, *, indent: int = 0):
        click.echo(" " * indent + s, file=self.stream)

    def report_success(self) -> None:
        ok = click.style("ok", fg="green") if self.color else "ok"
        self.echo(f"{ok} -- validation done")

    def _format_validation_error_message(
        self, err: jsonschema.ValidationError, filename: str | None = None
    ) -> str:
        error_loc = err.json_path
        if filename:
            error_loc = f"{filename}::{error_loc}"
        if self.color:
            error_loc = click.style(error_loc, fg="yellow")
        return f"{error_loc}: {err.message}"

    def _show_validation_error(
        self,
        filename: str,
        err: jsonschema.ValidationError,
    ) -> None:

        self.echo(
            self._format_validation_error_message(err, filename=filename), indent=2
        )
        if err.context:
            best_match = jsonschema.exceptions.best_match(err.context)
            self.echo("Underlying errors caused this.", indent=2)
            self.echo("Best Match:", indent=2)
            self.echo(self._format_validation_error_message(best_match), indent=4)
            if self.verbosity > 0:
                self.echo("All Errors:", indent=2)
                for err in iter_validation_error(err):
                    self.echo(self._format_validation_error_message(err), indent=4)

    def report_validation_errors(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
    ) -> None:
        self.echo("Schema validation errors were encountered.")
        for filename, errors in error_map.items():
            for err in errors:
                self._show_validation_error(filename, err)


class JsonReporter(Reporter):
    def __init__(self, *, pretty: bool | None = None, verbosity: int = 0) -> None:
        # default to pretty output if stdout is a tty and compact output if not
        self.pretty: bool = pretty if pretty is not None else sys.stdout.isatty()
        self.verbosity = verbosity

    def _dump(self, data: t.Any) -> None:
        if self.pretty:
            click.echo(json.dumps(data, indent=2, separators=(",", ": ")))
        else:
            click.echo(json.dumps(data, separators=(",", ":")))

    def report_success(self) -> None:
        self._dump({"status": "ok", "errors": []})

    def _dump_error_map(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
    ) -> t.Iterator[dict]:
        for filename, errors in error_map.items():
            for err in errors:
                item = {
                    "filename": filename,
                    "path": err.json_path,
                    "message": err.message,
                    "has_sub_errors": bool(err.context),
                }
                if err.context:
                    best_match = jsonschema.exceptions.best_match(err.context)
                    item["best_match"] = {
                        "path": best_match.json_path,
                        "message": best_match.message,
                    }
                    if self.verbosity > 0:
                        item["sub_errors"] = [
                            {"path": suberr.json_path, "message": suberr.message}
                            for suberr in iter_validation_error(err)
                        ]

                yield item

    def report_validation_errors(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
    ) -> None:
        self._dump(
            {
                "status": "fail",
                "errors": list(self._dump_error_map(error_map)),
            }
        )


REPORTER_BY_NAME: dict[str, type[Reporter]] = {
    "text": TextReporter,
    "json": JsonReporter,
}
