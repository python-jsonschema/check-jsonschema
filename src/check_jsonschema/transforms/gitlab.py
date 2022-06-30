from __future__ import annotations

import typing as t

from check_jsonschema.loaders.instance.yaml import YAML_IMPL


class GitLabReferenceExpectationViolation(ValueError):
    def __init__(self, msg: str, data: t.Any) -> None:
        super().__init__(
            f"check-jsonschema rejects this gitlab !reference tag: {msg}\n{data!r}"
        )


class GitLabReference:
    yaml_tag = "!reference"

    def __init__(self, data: list[str]) -> None:
        self.data = data

    @classmethod
    def from_yaml(cls, constructor, node):
        if not isinstance(node.value, list):
            raise GitLabReferenceExpectationViolation("non-list value", node)
        return [item.value for item in node.value]


# this "transform" is actually a no-op on the data, but it registers the GitLab !reference
# tag with the instance YAML loader
def gitlab_init() -> None:
    YAML_IMPL.register_class(GitLabReference)
