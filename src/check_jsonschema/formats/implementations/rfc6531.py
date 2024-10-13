import re

RFC6531_REGEX = re.compile(
    r"""
    ^
    # local part
    (
    ([0-9a-z!#$%&'*+-\/=?^_`\{|\}~\u0080-\U0010FFFF]+(\.[0-9a-z!#$%&'*+-\/=?^_`\{|\}~\u0080-\U0010FFFF]+)*)
    |
    # quoted string
    "([\x20-\x21\x23-\x5B\x5D-\x7E\u0080-\U0010FFFF]|\\[\x20-\x7E])*"
    )
    @
    # Domain/address
    (
    # Address literal
    (\[(
    # IPv4
    (\d{1,3}(\.\d{1,3}){3})
    |
    # IPv6
    (IPv6:[0-9a-f]{1,4}(:[0-9a-f]{1,4}){7})
    |
    (IPv6:([0-9a-f]{1,4}(:[0-9a-f]{1,4}){0,5})?::([0-9a-f]{1,4}(:[0-9a-f]{1,4}){0,5})?)
    |
    (IPv6:[0-9a-f]{1,4}(:[0-9a-f]{1,4}){5}:\d{1,3}(\.\d{1,3}){3})
    |
    (IPv6:([0-9a-f]{1,4}(:[0-9a-f]{1,4}){0,3})?::([0-9a-f]{1,4}(:[0-9a-f]{1,4}){0,3}:)?\d{1,3}(\.\d{1,3}){3})
    |
    # General address
    ([a-z0-9-]*[a-z0-9]:[\x21-\x5A\x5E-\x7E]+)
    )\])
    |
    # Domain
    ((?!.{256,})(([0-9a-z\u0080-\U0010FFFF]([0-9a-z-\u0080-\U0010FFFF]*[0-9a-z\u0080-\U0010FFFF])?))(\.([0-9a-z\u0080-\U0010FFFF]([0-9a-z-\u0080-\U0010FFFF]*[0-9a-z\u0080-\U0010FFFF])?))*)
    )
    $
    """,
    re.VERBOSE | re.UNICODE,
)


def validate(email_str: object) -> bool:
    """Validate a string as a RFC6531 email address."""
    if not isinstance(email_str, str):
        return False
    return RFC6531_REGEX.match(email_str)


if __name__ == "__main__":
    import timeit

    N = 100_000
    tests = (("basic", "user@example.com"),)

    print("benchmarking")
    for name, val in tests:
        all_times = timeit.repeat(
            f"validate({val!r})", globals=globals(), repeat=3, number=N
        )
        print(f"{name} (valid={validate(val)}): {int(min(all_times) / N * 10**9)}ns")
