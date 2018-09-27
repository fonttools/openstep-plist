#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

import array
from cpython cimport array
cimport cython
from .util cimport tounicode, tostr, unicode_array_template


@cython.final
cdef class Encoder:

    cdef public array.array buf

    def __cinit__(self):
        self.buf = array.clone(unicode_array_template, 0, zero=False)
