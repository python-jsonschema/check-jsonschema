from __future__ import annotations

import typing as t
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedDocument:
    data: t.Any
    line: int | None = None


@dataclass(frozen=True)
class MultiDocumentData:
    documents: tuple[ParsedDocument, ...]
