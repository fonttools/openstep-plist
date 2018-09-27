#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

import array
from cpython cimport array
from cpython.unicode cimport (
    PyUnicode_FromUnicode,
    PyUnicode_AS_UNICODE,
    PyUnicode_GET_SIZE,
)
from cpython.object cimport Py_SIZE
cimport cython

from .util cimport (
    unicode_array_template,
    is_valid_unquoted_string_char,
    isprint,
)


cdef inline bint is_valid_unquoted_string(const Py_UNICODE *a, Py_ssize_t length):
    cdef Py_ssize_t i
    for i in range(length):
        if not is_valid_unquoted_string_char(a[i]):
            return False
    return True


@cython.final
cdef class Writer:

    cdef public array.array dest
    cdef bint unicode_escape

    def __cinit__(self, unicode_escape=True):
        self.dest = array.clone(unicode_array_template, 0, zero=False)
        self.unicode_escape = unicode_escape

    def getvalue(self):
        return self._getvalue()

    def dump(self, file):
        # TODO encode to UTF-8 if binary file
        cdef unicode s = self._getvalue()
        file.write(s)

    def write(self, object obj):
        return self.write_object(obj)

    cdef inline unicode _getvalue(self):
        cdef array.array dest = self.dest
        return PyUnicode_FromUnicode(dest.data.as_pyunicodes, Py_SIZE(dest))

    cdef Py_ssize_t write_object(self, object obj) except -1:
        if obj is None:
            return self.write_string("(nil)")
        if isinstance(obj, unicode):
            return self.write_string(obj)
        else:
            # XXX
            assert 0

    cdef Py_ssize_t write_quoted_string(
        self, const Py_UNICODE *s, Py_ssize_t length
    ) except -1:

        cdef:
            array.array dest = self.dest
            bint unicode_escape = self.unicode_escape
            const Py_UNICODE *curr = s
            const Py_UNICODE *end = &s[length]
            Py_UNICODE *ptr
            unsigned long ch
            Py_ssize_t base_length = Py_SIZE(dest)
            Py_ssize_t new_length = 0

        while curr < end:
            ch = curr[0]
            if ch == c'\n' or ch == c'\t' or ch == c'\r':
                new_length += 1
            elif (
                ch == c'\a' or ch == c'\b' or ch == c'\v' or ch == c'\f'
                or ch == c'\\' or ch == c'"'
            ):
                new_length += 2
            else:
                if ch < 128:
                    if isprint(ch) or ch == c' ':
                        new_length += 1
                    else:
                        new_length += 4
                elif unicode_escape:
                    new_length += 6
                else:
                    new_length += 1
            curr += 1

        array.resize_smart(dest, base_length + new_length + 2)
        ptr = dest.data.as_pyunicodes + base_length
        ptr[0] = '"'
        ptr += 1

        curr = s
        while curr < end:
            ch = curr[0]
            if ch == c'\n' or ch == c'\t' or ch == c'\r':
                ptr[0] = ch
                ptr += 1
            elif ch == c'\a':
                ptr[0] = c'\\'; ptr[1] = c'a'; ptr += 2
            elif ch == c'\b':
                ptr[0] = c'\\'; ptr[1] = c'b'; ptr += 2
            elif ch == c'\v':
                ptr[0] = c'\\'; ptr[1] = c'v'; ptr += 2
            elif ch == c'\f':
                ptr[0] = c'\\'; ptr[1] = c'f'; ptr += 2
            elif ch == c'\\':
                ptr[0] = c'\\'; ptr[1] = c'\\'; ptr += 2
            elif ch == c'"':
                ptr[0] = c'\\'; ptr[1] = c'"'; ptr += 2
            else:
                if ch < 128:
                    if isprint(ch) or ch == c' ':
                        ptr[0] = ch
                        ptr += 1
                    else:
                        ptr[0] = c'\\'
                        ptr += 1
                        ptr[2] = (ch & 7) + c'0'
                        ch >>= 3
                        ptr[1] = (ch & 7) + c'0'
                        ch >>= 3
                        ptr[0] = (ch & 7) + c'0'
                        ptr += 3
                elif unicode_escape:
                    # doesn't handle characters > BMP with surrogate pairs
                    ptr[0] = c'\\'
                    ptr[1] = c'U'
                    ptr += 2
                    ptr[3] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
                    ch >>= 4
                    ptr[2] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
                    ch >>= 4
                    ptr[1] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
                    ch >>= 4
                    ptr[0] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
                    ptr += 4
                else:
                    ptr[0] = ch
                    ptr += 1

            curr += 1

        ptr[0] = c'"'

        return new_length + 2

    cdef Py_ssize_t write_string(self, unicode string) except -1:
        cdef:
            Py_UNICODE *s = PyUnicode_AS_UNICODE(string)
            Py_ssize_t length = PyUnicode_GET_SIZE(string)
            array.array dest = self.dest

        if length > 0 and is_valid_unquoted_string(s, length):
            array.extend_buffer(dest, <char *>s, length)
            return length
        else:
            return self.write_quoted_string(s, length)
