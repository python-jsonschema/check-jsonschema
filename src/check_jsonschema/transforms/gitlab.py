from __future__ import annotations

import typing as t

import ruamel.yaml

from ..parsers.yaml import YAMLDocuments
from .base import Transform


class GitLabReferenceExpectationViolation(ValueError):
    pass


class GitLabReference:
    yaml_tag = "!reference"

    @classmethod
    def from_yaml(
        cls, constructor: ruamel.yaml.BaseConstructor, node: ruamel.yaml.Node
    ) -> list[str]:
        if not isinstance(node.value, list):
            raise GitLabReferenceExpectationViolation(
                "check-jsonschema rejects this gitlab !reference tag: "
                f"non-list-value\n{node!r}"
            )
        return [item.value for item in node.value]


# Register GitLab's !reference tag and combine multi-document CI configuration.
class GitLabDataTransform(Transform):
    load_multiple_yaml_documents = True

    def modify_yaml_implementation(self, implementation: ruamel.yaml.YAML) -> None:
        implementation.register_class(GitLabReference)

    def __call__(self, data: t.Any) -> t.Any:
        if not isinstance(data, YAMLDocuments):
            return data
        documents = [document for document in data if document is not None]
        if not documents:
            return None
        if len(documents) == 1:
            return documents[0]
        if not all(isinstance(document, dict) for document in documents):
            return documents

        merged = {}
        for document in documents:
            merged.update(document)
        return merged


GITLAB_TRANSFORM = GitLabDataTransform()
