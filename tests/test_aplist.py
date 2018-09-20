from __future__ import absolute_import, unicode_literals
from .cdef_wrappers import (
    line_number_strings,
    is_valid_unquoted_string_char,
)


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
