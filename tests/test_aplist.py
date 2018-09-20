from __future__ import absolute_import, unicode_literals
import sys
from io import StringIO, BytesIO
from .cdef_wrappers import (
    line_number_strings,
    is_valid_unquoted_string_char,
    advance_to_non_space,
    get_slashed_char,
    parse_unquoted_plist_string,
    parse_plist_string,
)
import aplist

import pytest


def test_line_number_strings():
    assert line_number_strings("", 0) == 1
    assert line_number_strings("a\na", 1) == 1
    assert line_number_strings("a\na", 2) == 2
    assert line_number_strings("a\naa\n", 4) == 2
    assert line_number_strings("a\naa\na", 5) == 3
    assert line_number_strings("a\raa\ra", 5) == 3
    assert line_number_strings("a\r\naa\ra", 6) == 3
    assert line_number_strings("a\n\naa\n\na", 7) == 5


def test_is_valid_unquoted_string_char():
    assert is_valid_unquoted_string_char(ord("a"))
    assert is_valid_unquoted_string_char(ord("b"))
    assert is_valid_unquoted_string_char(ord("z"))
    assert is_valid_unquoted_string_char(ord("A"))
    assert is_valid_unquoted_string_char(ord("B"))
    assert is_valid_unquoted_string_char(ord("Z"))
    assert is_valid_unquoted_string_char(ord("_"))
    assert is_valid_unquoted_string_char(ord("$"))
    assert is_valid_unquoted_string_char(ord("/"))
    assert is_valid_unquoted_string_char(ord(":"))
    assert is_valid_unquoted_string_char(ord("."))
    assert is_valid_unquoted_string_char(ord("-"))
    assert not is_valid_unquoted_string_char(ord('"'))
    assert not is_valid_unquoted_string_char(ord(","))
    assert not is_valid_unquoted_string_char(ord("{"))
    assert not is_valid_unquoted_string_char(ord(")"))
    assert not is_valid_unquoted_string_char(ord(";"))
    assert not is_valid_unquoted_string_char(0x00)  # NULL
    assert not is_valid_unquoted_string_char(0x0A)  # \n
    assert not is_valid_unquoted_string_char(0x0D)  # \r


@pytest.mark.parametrize(
    "string, offset, expected",
    [
        ("", 0, None),
        (" a", 0, "a"),
        (" a", 1, "a"),
        (" a", 2, None),
        ("\t\ta", 1, "a"),
        ("\t\ta", 2, "a"),
        ("\t\ta", 3, None),
        ("abc//this is an inline comment", 3, None),
        ("abc //also this\n", 3, None),
        ("abc //this as well\n\nz", 3, "z"),
        ("abc/this is not a comment", 3, "/"),
        ("abc/", 3, "/"),  # not a comment either
        ("abcd /* C-style comments! */z", 4, "z")
    ]
)
def test_advance_to_non_space(string, offset, expected):
    assert advance_to_non_space(string, offset) == expected


@pytest.mark.parametrize(
    "string, expected",
    [
        ("000", "\x00"),
        ("001", "\x01"),
        ("002", "\x02"),
        ("003", "\x03"),
        ("004", "\x04"),
        ("005", "\x05"),
        ("006", "\x06"),
        ("007", "\x07"),
        ("012", "\n"),
        ("111", "I"),
        ("111", "I"),
        ("200", "\xa0"),
        ("201", "\xc0"),
        ("375", "\xff"),
        ("376", "\ufffd"),
        ("376", "\ufffd"),
        ("U0000", "\u0000"),
        ("U0001", "\u0001"),
        ("U0411", "\u0411"),
        ("U00FA", "\u00fa"),
        ("a", "\a"),
        ("b", "\b"),
        ("f", "\f"),
        ("n", "\n"),
        ("r", "\r"),
        ("t", "\t"),
        ("v", "\v"),
        ('"', '"'),
        ("\n", "\n"),
        ("\\", "\\"),
        ("z", "z"),
    ]
)
def test_get_slashed_char(string, expected):
    assert get_slashed_char(string) == expected


@pytest.mark.parametrize(
    "string, expected",
    [
        ("a", "a"),
        ("abc;", "abc"),  # trailing chars left in buffer
        ("1", "1"),
        ("123456789", "123456789"),
        ("1.23456789", "1.23456789"),
    ]
)
def test_parse_unquoted_plist_string(string, expected):
    assert parse_unquoted_plist_string(string) == expected


def test_parse_unquoted_plist_string_EOF():
    with pytest.raises(aplist.ParseError, match="Unexpected EOF"):
        parse_unquoted_plist_string("") == expected


@pytest.mark.parametrize(
    "string, expected",
    [
        ("a", "a"),
        ('"a"', "a"),
        ("'a'", "a")
    ]
)
def test_parse_plist_string(string, expected):
    assert parse_plist_string(string) == expected


def test_parse_plist_string_EOF():
    with pytest.raises(aplist.ParseError, match="Unexpected EOF"):
        parse_plist_string("")


def test_parse_plist_string_invalid_char():
    with pytest.raises(aplist.ParseError, match="Invalid string character"):
        parse_plist_string("\\")
    assert parse_plist_string("\\", required=False) is None


def test_parse_plist_array():
    assert aplist.loads("(1)") == ["1"]
    assert aplist.loads("(1,)") == ["1"]
    assert aplist.loads("(\t1  \r\n, 2.2, c,\n)") == ["1", "2.2", "c"]
    assert aplist.loads("('1', '2')") == ["1", "2"]
    assert aplist.loads('(\n1,\n"\'2\'"\n)') == ["1", "'2'"]


@pytest.mark.parametrize(
    "string, lineno",
    [
        ('(a ', 1),
        ('(a,\nb,\r\nc', 3),
    ]
)
def test_parse_plist_array_missing_comma(string, lineno):
    msg = "Missing ',' for array at line %d" % lineno
    with pytest.raises(aplist.ParseError, match=msg):
         aplist.loads(string)


@pytest.mark.parametrize(
    "string, lineno",
    [
        ('(a,', 1),
        ('(a,\nb, }', 2),
    ]
)
def test_parse_plist_array_missing_paren(string, lineno):
    msg = r"Expected terminating '\)' for array at line %d" % lineno
    with pytest.raises(aplist.ParseError, match=msg):
         aplist.loads(string)


def test_parse_plist_array_empty():
    assert aplist.loads("()") == []


def test_parse_plist_dict_empty():
    assert aplist.loads("") == {}
    assert aplist.loads("{}") == {}


@pytest.mark.parametrize(
    "string, expected",
    [
        ("{a=1;}", {"a": "1"}),
        ('{"a"="1";}', {"a": "1"}),
        ("{'a'='1';}", {"a": "1"}),
        ("{\na = 1;\n}", {"a": "1"}),
        ("{\na\n=\n1;\n}", {"a": "1"}),
        ("{a=1;b;}", {"a": "1", "b": "b"}),
    ]
)
def test_parse_plist_dict(string, expected):
    assert aplist.loads(string) == expected


def test_parse_plist_dict_invalid():
    msg = "Unexpected character after key at line 1: u?','"
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("{a,}")

    msg = "Missing ';' on line 1"
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("{b ")

    msg = "Missing ';' on line 2"
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("{b = zzz;\nc = xxx}")

    msg = "Expected terminating '}' for dictionary at line 3"
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("{b = zzz;\nc = xxx;\nd = jjj;")


@pytest.mark.parametrize(
    "string, expected",
    [
        ("<AA>", b"\xaa"),
        ("<B1B0AFBA>", b"\xb1\xb0\xaf\xba"),
        ("<AA BB>", b"\xaa\xbb"),
        ("<4142\n4344>", b"ABCD"),
    ]
)
def test_parse_plist_data(string, expected):
    assert aplist.loads(string) == expected


def test_parse_plist_data_invalid():
    with pytest.raises(aplist.ParseError, match="Expected terminating '>'"):
        aplist.loads("<FF")

    msg = "Malformed data byte group at line 1: invalid hex digit: u?'Z'"
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("<Z")
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("<AZ")

    msg = "Malformed data byte group at line 1: uneven length"
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("<AAA")
    with pytest.raises(aplist.ParseError, match=msg):
        aplist.loads("<AAA>")


def test_parse_plist_object_invalid():
    with pytest.raises(aplist.ParseError, match="Unexpected character"):
        aplist.loads(";")
    with pytest.raises(aplist.ParseError, match="Unexpected EOF while parsing plist"):
        aplist.loads("{a=")
    with pytest.raises(aplist.ParseError, match="Junk after plist at line 3"):
        aplist.loads("{a=1;\nb=2;\n}...")


def test_parse_string_resources():
    assert aplist.loads("a=1;\n'b' = 2.4;\n'c' = \"hello world\";") == {
        "a": "1", "b": "2.4", "c": "hello world"
    }


def test_load():
    fp = StringIO("{a=1;}")
    assert aplist.load(fp) == {"a": "1"}


def test_load_from_bytes():
    if sys.version_info.major < 3:
        assert aplist.loads(b"{a=1;}") == {"a": "1"}
    else:
        with pytest.raises(TypeError, match="Could not convert to unicode"):
            aplist.loads(b"{a=1;}")
