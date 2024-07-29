# Test email strings for validity
import json

import pytest

FORMAT_SCHEMA_EMAIL = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {"email": {"type": "string", "format": "email"}},
}
FORMAT_SCHEMA_IDN_EMAIL = {
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {"email": {"type": "string", "format": "idn-email"}},
}

ALWAYS_PASSING_EMAILS = [
    {"email": r"simple@example.com"},
    {"email": r"very.common@example.com"},
    {"email": r"FirstName.LastName@EasierReading.org"},
    {"email": r"x@example.com"},
    {"email": r"long.email-address-with-hyphens@and.subdomains.example.com"},
    {"email": r"user.name+tag+sorting@example.com"},
    {"email": r"name/surname@example.com"},
    {"email": r"admin@example"},
    {"email": r"example@s.example"},
    {"email": r'" "@example.org'},
    {"email": r'"john..doe"@example.org'},
    {"email": r"mailhost!username@example.org"},
    {
        "email": r'"very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com'
    },
    {"email": r"user%example.com@example.org"},
    {"email": r"user-@example.org"},
    {"email": r"postmaster@[123.123.123.123]"},
    {"email": r"postmaster@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]"},
    {"email": r"_test@[IPv6:2001:0db8:85a3:0000:0000:8a2e:0370:7334]"},
]

IDN_ONLY_EMAILS = [
    {"email": r"I❤️CHOCOLATE@example.com"},
]

ALWAYS_FAILING_EMAILS = [
    {"email": r"abc.example.com"},
    {"email": r"a@b@c@example.com"},
    {"email": r'a"b(c)d,e:f;g<h>i[j\k]l@example.com'},
    {"email": r'just"not"right@example.com'},
    {"email": r'this is"not\allowed@example.com'},
    {"email": r"this\ still\"not\\allowed@example.com"},
    {
        "email": r"1234567890123456789012345678901234567890123456789012345678901234+x@example.com"
    },
    {"email": r"i.like.underscores@but_they_are_not_allowed_in_this_part"},
    {
        "email": r"trythis@123456789012345678901234567890123456789012345678901234567890123456.com"
    },
    {
        "email": r"another@12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234.com"
    },
]


def test_email_format_good(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA_EMAIL))

    for idx, email_doc in enumerate(ALWAYS_PASSING_EMAILS):
        doc = tmp_path / f"doc{idx}.json"
        doc.write_text(json.dumps(email_doc))
        res = run_line(
            [
                "check-jsonschema",
                "--schemafile",
                str(schemafile),
                str(doc),
            ],
        )
        assert (email_doc["email"], res.exit_code) == (email_doc["email"], 0)


def test_email_format_bad(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA_EMAIL))

    for idx, email_doc in enumerate(ALWAYS_FAILING_EMAILS + IDN_ONLY_EMAILS):
        doc = tmp_path / f"doc{idx}.json"
        doc.write_text(json.dumps(email_doc))
        res = run_line(
            [
                "check-jsonschema",
                "--schemafile",
                str(schemafile),
                str(doc),
            ],
        )
        assert (email_doc["email"], res.exit_code) != (email_doc["email"], 0)


def test_idn_email_format_good(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA_IDN_EMAIL))

    for idx, email_doc in enumerate(ALWAYS_PASSING_EMAILS + IDN_ONLY_EMAILS):
        doc = tmp_path / f"doc{idx}.json"
        doc.write_text(json.dumps(email_doc))
        res = run_line(
            [
                "check-jsonschema",
                "--schemafile",
                str(schemafile),
                str(doc),
            ],
        )
        assert (email_doc["email"], res.exit_code) == (email_doc["email"], 0)


def test_idn_email_format_bad(run_line, tmp_path):
    schemafile = tmp_path / "schema.json"
    schemafile.write_text(json.dumps(FORMAT_SCHEMA_IDN_EMAIL))

    for idx, email_doc in enumerate(ALWAYS_FAILING_EMAILS):
        doc = tmp_path / f"doc{idx}.json"
        doc.write_text(json.dumps(email_doc))
        res = run_line(
            [
                "check-jsonschema",
                "--schemafile",
                str(schemafile),
                str(doc),
            ],
        )
        assert (email_doc["email"], res.exit_code) != (email_doc["email"], 0)
