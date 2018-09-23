#cython: language_level=3

from libc.stdint cimport uint32_t
from cpython cimport array


cdef extern from "<ctype.h>":
    int isxdigit(int c)
    int isdigit(int c)


ctypedef struct ParseInfo:
    const Py_UNICODE *begin
    const Py_UNICODE *curr
    const Py_UNICODE *end
    void *dict_type


cdef class ParseError(Exception):
    pass


cdef uint32_t line_number_strings(ParseInfo *pi)


cdef bint is_valid_unquoted_string_char(Py_UNICODE x)


cdef bint advance_to_non_space(ParseInfo *pi)


cdef Py_UNICODE get_slashed_char(ParseInfo *pi)


cdef unicode parse_quoted_plist_string(ParseInfo *pi, Py_UNICODE quote)


cdef unicode parse_unquoted_plist_string(ParseInfo *pi)


cdef unicode parse_plist_string(ParseInfo *pi, required=*)


cdef list parse_plist_array(ParseInfo *pi)


cdef object parse_plist_dict_content(ParseInfo *pi)


cdef object parse_plist_dict(ParseInfo *pi)


cdef unsigned char from_hex_digit(unsigned char ch)


cdef array.array get_data_bytes(ParseInfo *pi)


cdef bytes parse_plist_data(ParseInfo *pi)


cdef object parse_plist_object(ParseInfo *pi, bint required=*)
