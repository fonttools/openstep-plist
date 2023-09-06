#cython: language_level=3


cdef bint string_needs_quotes(const Py_UCS4 *a, Py_ssize_t length)
