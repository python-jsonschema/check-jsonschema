"""
The reporter is an output formatter.
It takes the result of validation and reports it back to the user.
"""

from __future__ import annotations

import abc
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
        show_all_errors: bool = False,
    ) -> None:
        raise NotImplementedError


class TextReporter(Reporter):
    def __init__(self, *, stream: t.TextIO | None = None) -> None:
        # default stream is stdout (None)
        self.stream = stream

    def echo(self, s: str, *, indent: int = 0):
        click.echo(" " * indent + s, file=self.stream)

    def report_success(self) -> None:
        self.echo("ok -- validation done")

    def _format_validation_error_message(
        self, err: jsonschema.ValidationError, filename: str | None = None
    ) -> str:
        error_loc = err.json_path
        if filename:
            error_loc = f"{filename}::{error_loc}"
        return click.style(error_loc, fg="yellow") + f": {err.message}"

    def _show_validation_error(
        self,
        filename: str,
        err: jsonschema.ValidationError,
        show_all_errors: bool = False,
    ) -> None:

        self.echo(
            self._format_validation_error_message(err, filename=filename), indent=2
        )
        if err.context:
            best_match = jsonschema.exceptions.best_match(err.context)
            self.echo("Underlying errors caused this.", indent=2)
            self.echo("Best Match:", indent=2)
            self.echo(self._format_validation_error_message(best_match), indent=4)
            if show_all_errors:
                self.echo("All Errors:", indent=2)
                for err in iter_validation_error(err):
                    self.echo(self._format_validation_error_message(err), indent=4)

    def report_validation_errors(
        self,
        error_map: dict[str, list[jsonschema.ValidationError]],
        show_all_errors: bool = False,
    ) -> None:
        self.echo("Schema validation errors were encountered.")
        for filename, errors in error_map.items():
            for err in errors:
                self._show_validation_error(
                    filename, err, show_all_errors=show_all_errors
                )
