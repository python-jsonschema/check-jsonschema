from __future__ import annotations

import typing as t


def _githubusercontent_url(owner: str, repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


# this lists custom schemas which are *not* part of the catalog
CUSTOM_SCHEMA_NAMES = [
    "github-workflows-require-timeout",
]

# Known configs. The SchemaCatalog lists known schema URLs with their names.
# kept in alphabetical order by name
#
# Additional config could be associated with the schemas in the future.
SCHEMA_CATALOG: dict[str, dict[str, t.Any]] = {
    "azure-pipelines": {
        "url": _githubusercontent_url(
            "microsoft", "azure-pipelines-vscode", "main", "service-schema.json"
        ),
        "hook_config": {
            "name": "Validate Azure Pipelines",
            "description": "Validate Azure Pipelines config against the schema provided "
            "by Microsoft",
            "add_args": ["--data-transform", "azure-pipelines"],
            "files": r"^(\.)?azure-pipelines.(yml|yaml)$",
            "types": "yaml",
        },
    },
    "bamboo-spec": {
        "url": "https://json.schemastore.org/bamboo-spec.json",
        "hook_config": {
            "name": "Validate Bamboo Specs",
            "files": r"^bamboo-specs/.*\.(yml|yaml)$",
            "types": "yaml",
        },
    },
    "buildkite": {
        "url": _githubusercontent_url(
            "buildkite", "pipeline-schema", "main", "schema.json"
        ),
        "hook_config": {
            "name": "Validate Buildkite Pipelines",
            "description": (
                "Validate Buildkite Pipelines against the schema provided by Buildkite"
            ),
            "files": [
                r"buildkite\.(yml|yaml|json)",
                r"buildkite\.(.+)\.(yml|yaml|json)",
                r"(.*/)?\.buildkite/pipeline\.(yml|yaml|json)",
                r"(.*/)?\.buildkite/pipeline\.(.+)\.(yml|yaml|json)",
            ],
            "types_or": ["json", "yaml"],
        },
    },
    "dependabot": {
        "url": "https://json.schemastore.org/dependabot-2.0.json",
        "hook_config": {
            "name": "Validate Dependabot Config (v2)",
            "files": r"^\.github/dependabot.(yml|yaml)$",
            "types": "yaml",
        },
    },
    "github-actions": {
        "url": "https://json.schemastore.org/github-action",
        "hook_config": {
            "name": "Validate GitHub Actions",
            "files": ["action.(yml|yaml)", r"\.github/actions/(.+/)?action.(yml|yaml)"],
            "types": "yaml",
        },
    },
    "github-workflows": {
        "url": "https://json.schemastore.org/github-workflow",
        "hook_config": {
            "name": "Validate GitHub Workflows",
            "files": r"^\.github/workflows/[^/]+$",
            "types": "yaml",
        },
    },
    "gitlab-ci": {
        "url": "https://gitlab.com/gitlab-org/gitlab/-/raw/master/app/assets/javascripts"
        "/editor/schema/ci.json",
        "hook_config": {
            "name": "Validate GitLab CI config",
            "add_args": ["--data-transform", "gitlab-ci"],
            "files": r"^.*\.gitlab-ci.yml$",
            "types": "yaml",
        },
    },
    "readthedocs": {
        "url": _githubusercontent_url(
            "readthedocs",
            "readthedocs.org",
            "master",
            "readthedocs/rtd_tests/fixtures/spec/v2/schema.json",
        ),
        "hook_config": {
            "name": "Validate ReadTheDocs Config",
            "description": "Validate ReadTheDocs config against the schema "
            "provided by ReadTheDocs",
            "files": r"^\.readthedocs.(yml|yaml)$",
            "types": "yaml",
        },
    },
    "renovate": {
        "url": "https://docs.renovatebot.com/renovate-schema.json",
        "hook_config": {
            "name": "Validate Renovate Config",
            "description": "Validate Renovate config against the schema provided by "
            "Renovate (does not support renovate config in package.json)",
            "files": [
                r"renovate\.(json|json5)",
                r"\.(github|gitlab)/renovate\.(json|json5)",
                r"\.renovaterc(\.json)?",
            ],
        },
    },
    "travis": {
        "url": "https://json.schemastore.org/travis",
        "hook_config": {
            "name": "Validate Travis Config",
            "files": r"^\.travis.(yml|yaml)$",
            "types": "yaml",
        },
    },
}
