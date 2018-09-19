#cython: language_level=3, linetrace=True


ctypedef struct ParseInfo:
    const Py_UNICODE *begin
    const Py_UNICODE *curr
    const Py_UNICODE *end

cdef bint is_valid_unquoted_string_char(Py_UNICODE x)
