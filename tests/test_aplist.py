from __future__ import absolute_import, unicode_literals
from .cdef_wrappers import (
    line_number_strings,
    is_valid_unquoted_string_char,
    advance_to_non_space,
    get_slashed_char,
)
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
