import typing as t


def _githubusercontent_url(owner: str, repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


# Known configs. The SchemaCatalog lists known schema URLs with their names.
# kept in alphabetical order by name
#
# Additional config could be associated with the schemas in the future.
SCHEMA_CATALOG: t.Dict[str, t.Dict[str, t.Any]] = {
    "azure-pipelines": {
        "url": _githubusercontent_url(
            "microsoft", "azure-pipelines-vscode", "main", "service-schema.json"
        ),
    },
    "bamboo-spec": {
        "url": "https://json.schemastore.org/bamboo-spec.json",
    },
    "github-actions": {
        "url": "https://json.schemastore.org/github-action",
    },
    "github-workflows": {
        "url": "https://json.schemastore.org/github-workflow",
    },
    "gitlab-ci": {
        "url": "https://www.schemastore.org/schemas/json/gitlab-ci.json",
    },
    "readthedocs": {
        "url": _githubusercontent_url(
            "readthedocs",
            "readthedocs.org",
            "master",
            "readthedocs/rtd_tests/fixtures/spec/v2/schema.json",
        ),
    },
    "renovate": {
        "url": "https://docs.renovatebot.com/renovate-schema.json",
    },
    "travis": {
        "url": "https://json.schemastore.org/travis",
    },
}
