#cython: language_level=3, linetrace=True

from aplist cimport is_valid_unquoted_string_char


def test_is_valid_unquoted_string_char(x):
    r"""
    >>> test_is_valid_unquoted_string_char(ord("a"))
    True
    >>> test_is_valid_unquoted_string_char(ord("b"))
    True
    >>> test_is_valid_unquoted_string_char(ord("z"))
    True
    >>> test_is_valid_unquoted_string_char(ord("A"))
    True
    >>> test_is_valid_unquoted_string_char(ord("B"))
    True
    >>> test_is_valid_unquoted_string_char(ord("Z"))
    True
    >>> test_is_valid_unquoted_string_char(ord("_"))
    True
    >>> test_is_valid_unquoted_string_char(ord("$"))
    True
    >>> test_is_valid_unquoted_string_char(ord("/"))
    True
    >>> test_is_valid_unquoted_string_char(ord(":"))
    True
    >>> test_is_valid_unquoted_string_char(ord("."))
    True
    >>> test_is_valid_unquoted_string_char(ord("-"))
    True
    >>> test_is_valid_unquoted_string_char(ord('"'))
    False
    >>> test_is_valid_unquoted_string_char(ord(","))
    False
    >>> test_is_valid_unquoted_string_char(ord("{"))
    False
    >>> test_is_valid_unquoted_string_char(ord(")"))
    False
    >>> test_is_valid_unquoted_string_char(ord(";"))
    False
    >>> test_is_valid_unquoted_string_char(0)  # \n
    False
    >>> test_is_valid_unquoted_string_char(10)  # \n
    False
    >>> test_is_valid_unquoted_string_char(13)  # \r
    False
    """
    return is_valid_unquoted_string_char(x)



