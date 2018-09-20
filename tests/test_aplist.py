from __future__ import absolute_import, unicode_literals
from .cdef_wrappers import is_valid_unquoted_string_char


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
