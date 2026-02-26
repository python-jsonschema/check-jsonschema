from __future__ import annotations

import ruamel.yaml

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


# this "transform" is actually a no-op on the data, but it registers the GitLab !reference
# tag with the instance YAML loader
class GitLabDataTransform(Transform):
    def modify_yaml_implementation(self, implementation: ruamel.yaml.YAML) -> None:
        implementation.register_class(GitLabReference)


GITLAB_TRANSFORM = GitLabDataTransform()
