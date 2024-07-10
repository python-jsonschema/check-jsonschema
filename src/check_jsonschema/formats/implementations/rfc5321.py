import re

RFC5321_REGEX = re.compile(
    r"""
    ^
    (
    [!#-'*+/-9=?A-Z^-~-]+(\.[!#-'*+/-9=?A-Z^-~-]+)*
    |
    "([]!#-[^-~ \t]|(\\[\t -~]))+"
    )
    @
    (
    [!#-'*+/-9=?A-Z^-~-]+(\.[!#-'*+/-9=?A-Z^-~-]+)*
    |
    \[[\t -Z^-~]*]
    )
    $
""",
    re.VERBOSE | re.ASCII,
)


def validate(email_str: object) -> bool:
    """Validate a string as a RFC5321 email address."""
    if not isinstance(email_str, str):
        return False
    return not not RFC5321_REGEX.match(email_str)


if __name__ == "__main__":
    import timeit

    N = 100_000
    tests = (
        ("basic", "user@example.com"),
    )

    print("benchmarking")
    for name, val in tests:
        all_times = timeit.repeat(
            f"validate({val!r})", globals=globals(), repeat=3, number=N
        )
        print(f"{name} (valid={validate(val)}): {int(min(all_times) / N * 10**9)}ns")
