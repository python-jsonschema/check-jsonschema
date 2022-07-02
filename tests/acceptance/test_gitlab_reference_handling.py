def test_gitlab_reference_handling_on_bad_data(run_line, tmp_path):
    doc = tmp_path / "data.yml"
    doc.write_text(
        """\
include:
  - local: setup.yml

test:
  script:
    # !reference not a list, error
    - !reference .setup
    - echo running my own command
"""
    )

    res = run_line(
        [
            "check-jsonschema",
            "--builtin-schema",
            "gitlab-ci",
            "--data-transform",
            "gitlab-ci",
            str(doc),
        ],
        catch_exceptions=True,
    )
    assert res.exit_code == 1
