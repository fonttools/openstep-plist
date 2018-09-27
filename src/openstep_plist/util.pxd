#cython: language_level=3

from cpython cimport array


cdef extern from "<ctype.h>":
    int isxdigit(int c)
    int isdigit(int c)
    int isprint(int c)


cdef unicode tounicode(s, encoding=*, errors=*)


cdef tostr(s, encoding=*, errors=*)


cdef array.array unicode_array_template


cdef bint is_valid_unquoted_string_char(Py_UNICODE x)
