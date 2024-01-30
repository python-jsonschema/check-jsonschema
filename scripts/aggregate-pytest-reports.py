import argparse
import sys
from collections import defaultdict
from xml.etree import ElementTree  # nosec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILES", nargs="+")
    args = parser.parse_args()

    tests_by_name = defaultdict(dict)
    skipped_module_counts = defaultdict(int)
    for filename in args.FILES:
        tree = ElementTree.parse(filename)
        root = tree.getroot()

        for testcase in root.findall("./testsuite/testcase"):
            classname = testcase.get("classname")
            name = testcase.get("name")

            skip_node = testcase.find("skipped")

            if classname:
                nodename = f"{classname.replace('.', '/')}.py::{name}"
                if skip_node is not None:
                    if "skipped" not in tests_by_name[nodename]:
                        tests_by_name[nodename]["skipped"] = True
                else:
                    tests_by_name[nodename]["skipped"] = False
            else:
                if skip_node is not None:
                    skipped_module_counts[name] += 1

    skipped_modules = {
        modname
        for modname, count in skipped_module_counts.items()
        if count == len(args.FILES)
    }

    fail = False
    for nodename, attributes in tests_by_name.items():
        if attributes.get("skipped") is True:
            print(f"ALWAYS SKIPPED: {nodename}")
            fail = True

    if skipped_modules:
        for modname in skipped_modules:
            print(f"ALWAYS SKIPPED MODULE: {modname}")
        fail = True

    if fail:
        print("fail")
        sys.exit(1)
    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
