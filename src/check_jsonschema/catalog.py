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
    "dependabot": {
        "url": "https://json.schemastore.org/dependabot-2.0.json",
        "hook_config": {
            "name": "Validate Dependabot Config (v2)",
            "files": r"^\.github/dependabot.yml$",
            "types": "yaml",
        },
    },
    "github-actions": {
        "url": "https://json.schemastore.org/github-action",
        "hook_config": {
            "name": "Validate GitHub Actions",
            "files": ["action.(yml|yaml)", r"\.github/actions/.*"],
            "types": "yaml",
        },
    },
    "github-workflows": {
        "url": "https://json.schemastore.org/github-workflow",
        "hook_config": {
            "name": "Validate GitHub Workflows",
            "files": r"^\.github/workflows/",
            "types": "yaml",
        },
    },
    "gitlab-ci": {
        "url": "https://gitlab.com/gitlab-org/gitlab/-/raw/master/app/assets/javascripts"
        "/editor/schema/ci.json",
        "hook_config": {
            "name": "Validate GitLab CI config",
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
    "pre-commit-config": {
        "url": "https://json.schemastore.org/pre-commit-config",
        "hook_config": {
            "name": "Validate .pre-comit-config.yaml",
            "files": r"^\.pre-commit-config\.ya?ml$",
            "types": "yaml"
        }
    },
    "pre-commit-hooks": {
        "url": "https://json.schemastore.org/pre-commit-hooks",
        "hook_config": {
            "name": "Validate .pre-comit-hooks.yaml",
            "files": r"^\.pre-commit-hooks\.ya?ml$",
            "types": "yaml"
        }
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
