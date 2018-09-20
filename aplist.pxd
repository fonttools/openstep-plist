#cython: language_level=3, linetrace=True


cdef extern from "<ctype.h>":
    int isxdigit(int c)
    int isdigit(int c)


ctypedef struct ParseInfo:
    const Py_UNICODE *begin
    const Py_UNICODE *curr
    const Py_UNICODE *end
    void *dict_type

cdef bint is_valid_unquoted_string_char(Py_UNICODE x)
