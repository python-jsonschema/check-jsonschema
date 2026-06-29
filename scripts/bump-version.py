#!/usr/bin/env python
# /// script
# dependencies = ["mddj==0.6.0", "packaging"]
# ///
import re
import sys

import mddj.api
from packaging.version import Version

DJ = mddj.api.DJ()


def replace_version(filename, formatstr, old_version, new_version):
    print(f"updating {filename}")
    with open(filename) as fp:
        content = fp.read()
    old_str = formatstr.format(old_version)
    new_str = formatstr.format(new_version)
    content = content.replace(old_str, new_str)
    with open(filename, "w") as fp:
        fp.write(content)


def update_changelog(new_version):
    print("updating CHANGELOG.rst")
    with open("CHANGELOG.rst") as fp:
        content = fp.read()

    vendor_marker = ".. vendor-insert-here"

    content = re.sub(
        r"""
Unreleased
----------
(\s*\n)+""" + re.escape(vendor_marker),
        f"""
Unreleased
----------

{vendor_marker}

{new_version}
{"-" * len(new_version)}""",
        content,
    )
    with open("CHANGELOG.rst", "w") as fp:
        fp.write(content)


def main():
    if len(sys.argv) != 2:
        sys.exit(2)

    new_version = sys.argv[1]
    old_version = DJ.read.version()
    print(f"old = {old_version}, new = {new_version}")
    assert Version(new_version) > Version(old_version)

    DJ.write.version(new_version)
    replace_version("README.md", "rev: {}", old_version, new_version)
    replace_version("docs/precommit_usage.rst", "rev: {}", old_version, new_version)
    replace_version("docs/optional_parsers.rst", "rev: {}", old_version, new_version)
    update_changelog(new_version)


if __name__ == "__main__":
    main()
