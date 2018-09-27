#cython: language_level=3

from cpython cimport array


cdef unicode tounicode(s, encoding=*, errors=*)


cdef tostr(s, encoding=*, errors=*)


cdef array.array unicode_array_template
