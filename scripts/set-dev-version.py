#!/usr/bin/env python
import argparse
import re


def get_old_version():
    with open("setup.cfg") as fp:
        content = fp.read()
    match = re.search(r"^version = (\d+\.\d+\.\d+)$", content, flags=re.MULTILINE)
    assert match
    return match.group(1)


def replace_version(old_version, new_version):
    print(f"updating setup.cfg version to {new_version}")
    with open("setup.cfg") as fp:
        content = fp.read()
    old_str = f"version = {old_version}"
    new_str = f"version = {new_version}"
    content = content.replace(old_str, new_str)
    with open("setup.cfg", "w") as fp:
        fp.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--number", help="dev number to use, defaults to 1", type=int, default=1
    )
    args = parser.parse_args()

    old_version = get_old_version()
    new_version = old_version + f".dev{args.number}"

    replace_version(old_version, new_version)
    print("done")


if __name__ == "__main__":
    main()
