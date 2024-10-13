import re

# ([!#-'*+/-9=?A-Z^-~-]+(\.[!#-'*+/-9=?A-Z^-~-]+)*|"([]!#-[^-~ \t]|(\\[\t -~]))+")
# @
# ([!#-'*+/-9=?A-Z^-~-]+(\.[!#-'*+/-9=?A-Z^-~-]+)*|\[[\t -Z^-~]*])
#
# [a-zA-Z0-9!#$%&'*+/=?^_`{|}~-] == Alphanumeric characters and most special characters except [ (),.:;<>@\[\]\t]
# [a-zA-Z0-9 !#$%&'()*+,./:;<=>?@\[\]^_`{|}~\t-] == All printable characters except for " and \
# [\t -~] == All printable characters
# [a-zA-Z0-9 !"#$%&'()*+,./:;<=>?@^_`{|}~\t-] == All printable characters except for the following characters []\
RFC5321_REGEX = re.compile(
    r"""
    ^
    (?P<local>
    [a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*
    |
    "(?:[a-zA-Z0-9 !#$%&'()*+,./:;<=>?@\[\]^_`{|}~\t-]|\\[\t -~])+"
    )
    @
    (?P<domain>
    [a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*
    |
    \[[a-zA-Z0-9 !"#$%&'()*+,./:;<=>?@^_`{|}~\t-]*\]
    )
    $
    """,
    re.VERBOSE | re.ASCII,
)


def validate(email_str: object) -> bool:
    """Validate a string as a RFC5321 email address."""
    if not isinstance(email_str, str):
        return False
    match = RFC5321_REGEX.match(email_str)
    if not match:
        return False
    local, domain = match.group("local", "domain")
    # Local part of email address is limited to 64 octets
    if len(local) > 64:
        return False
    # Domain names are limited to 253 octets
    if len(domain) > 253:
        return False
    for domain_part in domain.split("."):
        # DNS Labels are limited to 63 octets
        if len(domain_part) > 63:
            return False
    return True


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
