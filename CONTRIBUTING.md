# Contributing Guidelines

Interested in contributing to `check-jsonschema`? That's great!

## Questions, Feature Requests, Bug Reports, and Feedback...

…should be reported the [Issue Tracker](https://github.com/sirosen/check-jsonschema/issues)_

## Contributing Code

If you want to help work on the code, here are a few tips for getting setup.

### Testing

Testing is done with `tox`. To run the tests, just run

    tox

and a full test run will execute.

### pre-commit linting

`check-jsonschema` lints with [`pre-commit`](pre-commit.com).
To setup the `pre-commit` integration, first ensure you have it installed

    pipx install pre-commit

Then setup the hooks:

    pre-commit install

### pre-commit hook test cases

There are example files for the various pre-commit hooks defined in
`tests/example-files/`.

The `positive/` test cases should pass the hook with the matching name, and
the `negative/` test cases should fail the hook with the matching name.

These files are automatically picked up by the testsuite and checked.

## Documentation

All of the features of `check-jsonschema` should be documented in the readme
and changelog. If you notice missing documentation, that's a bug!
