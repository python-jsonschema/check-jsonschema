"""
Output formatters are called "reporters" because they take the result of validation
and report it back to the user.
"""

from __future__ import annotations

import abc
import json
import typing as t

import click
import jsonschema

from .utils import iter_validation_error


class Reporter(abc.ABC):
    def __init__(self, *, verbosity: int, **kwargs: t.Any) -> None:
        self.verbosity = verbosity
        super().__init__(**kwargs)

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
        verbosity: int,
        stream: t.TextIO | None = None,  # default stream is stdout (None)
        color: bool = True,
    ) -> None:
        super().__init__(verbosity=verbosity)
        self.stream = stream
        self.color = color

    def _echo(self, s: str, *, indent: int = 0) -> None:
        click.echo(" " * indent + s, file=self.stream)

    def report_success(self) -> None:
        if self.verbosity < 1:
            return
        ok = click.style("ok", fg="green") if self.color else "ok"
        self._echo(f"{ok} -- validation done")

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
        self._echo(
            self._format_validation_error_message(err, filename=filename), indent=2
        )
        if err.context:
            best_match = jsonschema.exceptions.best_match(err.context)
            self._echo("Underlying errors caused this.", indent=2)
            self._echo("Best Match:", indent=2)
            self._echo(self._format_validation_error_message(best_match), indent=4)
            if self.verbosity > 1:
                self._echo("All Errors:", indent=2)
                for err in iter_validation_error(err):
                    self._echo(self._format_validation_error_message(err), indent=4)

    def report_validation_errors(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
    ) -> None:
        if self.verbosity < 1:
            return
        self._echo("Schema validation errors were encountered.")
        for filename, errors in error_map.items():
            for err in errors:
                self._show_validation_error(filename, err)


class JsonReporter(Reporter):
    def __init__(self, *, verbosity: int, pretty: bool = True) -> None:
        super().__init__(verbosity=verbosity)
        # default to pretty output, can add a switch to disable this in the future
        self.pretty = pretty

    def _dump(self, data: t.Any) -> None:
        if self.pretty:
            click.echo(json.dumps(data, indent=2, separators=(",", ": ")))
        else:
            click.echo(json.dumps(data, separators=(",", ":")))

    def report_success(self) -> None:
        report_obj: dict[str, t.Any] = {"status": "ok"}
        if self.verbosity > 0:
            report_obj["errors"] = []
        self._dump(report_obj)

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
                    if self.verbosity > 1:
                        item["sub_errors"] = [
                            {"path": suberr.json_path, "message": suberr.message}
                            for suberr in iter_validation_error(err)
                        ]

                yield item

    def report_validation_errors(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
    ) -> None:
        report_obj: dict[str, t.Any] = {"status": "fail"}
        if self.verbosity > 0:
            report_obj["errors"] = list(self._dump_error_map(error_map))
        self._dump(report_obj)


REPORTER_BY_NAME: dict[str, type[Reporter]] = {
    "text": TextReporter,
    "json": JsonReporter,
}
