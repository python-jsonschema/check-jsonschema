import pytest

from check_jsonschema.formats.implementations.rfc6531 import validate


@pytest.mark.parametrize(
    "emailstr",
    (
        r"simple@example.com",
        r"very.common@example.com",
        r"FirstName.LastName@EasierReading.org",
        r"x@example.com",
        r"long.email-address-with-hyphens@and.subdomains.example.com",
        r"user.name+tag+sorting@example.com",
        r"name/surname@example.com",
        r"admin@example",
        r"example@s.example",
        r'" "@example.org',
        r'"john..doe"@example.org',
        r"mailhost!username@example.org",
        (
        r'"very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com'
        r"user%example.com@example.org"
    ),
        r"user-@example.org",
        r"postmaster@[123.123.123.123]",
        r"postmaster@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]",
        r"_test@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]",
        r"I❤️CHOCOLATE@example.com",
        r"用户@例子.广告",
        r"ಬೆಂಬಲ@ಡೇಟಾಮೇಲ್.ಭಾರತ",
        r"अजय@डाटा.भारत",
        r"квіточка@пошта.укр",
        r"χρήστης@παράδειγμα.ελ",
        r"Dörte@Sörensen.example.com",
        r"коля@пример.рф",
    ),
)
def test_simple_positive_cases(emailstr):
    assert validate(emailstr)


@pytest.mark.parametrize(
    "emailstr",
    (
        r"abc.example.com",
        r"a@b@c@example.com",
        r'a"b(c)d,e:f;g<h>i[j\k]l@example.com',
        r'just"not"right@example.com',
        r'this is"not\allowed@example.com',
        r"this\ still\"not\\allowed@example.com",
        r"1234567890123456789012345678901234567890123456789012345678901234+x@example.com",
        r"i.like.underscores@but_they_are_not_allowed_in_this_part",
        r"trythis@123456789012345678901234567890123456789012345678901234567890123456.com",
        r"another@12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234.com",
    ),
)
def test_simple_negative_case(emailstr):
    assert not validate(emailstr)
