#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

import array
from cpython cimport array
from cpython.unicode cimport (
    PyUnicode_FromUnicode,
    PyUnicode_AS_UNICODE,
    PyUnicode_AS_DATA,
    PyUnicode_GET_SIZE,
)
from cpython.object cimport Py_SIZE
from libc.stdint cimport uint16_t
cimport cython

from .util cimport (
    unicode_array_template,
    is_valid_unquoted_string_char,
    isprint,
    PY_NARROW_UNICODE,
    high_surrogate_from_unicode_scalar,
    low_surrogate_from_unicode_scalar,
)


cdef inline bint is_valid_unquoted_string(const Py_UNICODE *a, Py_ssize_t length):
    cdef Py_ssize_t i
    for i in range(length):
        if not is_valid_unquoted_string_char(a[i]):
            return False
    return True


cdef inline void escape_unicode(uint16_t ch, Py_UNICODE *dest):
    # caller must ensure 'dest' has rooms for 6 more Py_UNICODE
    dest[0] = c'\\'
    dest[1] = c'U'
    dest[5] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
    ch >>= 4
    dest[4] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
    ch >>= 4
    dest[3] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48
    ch >>= 4
    dest[2] = (ch & 15) + 55 if (ch & 15) > 9 else (ch & 15) + 48


@cython.final
cdef class Writer:

    cdef public array.array dest
    cdef bint unicode_escape
    cdef int float_precision

    def __cinit__(self, bint unicode_escape=True, int float_precision=6):
        self.dest = array.clone(unicode_array_template, 0, zero=False)
        self.unicode_escape = unicode_escape
        self.float_precision = float_precision

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
        elif isinstance(obj, bool):
            self.dest.append("1" if obj else "0")
            return 1
        elif isinstance(obj, float):
            return self.write_short_float_repr(obj)
        elif isinstance(obj, (int, long)):
            return self.write_unquoted_string(unicode(obj))
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
                    if ch > 0xFFFF and not PY_NARROW_UNICODE:
                        new_length += 12
                    else:
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
                    if ch > 0xFFFF and not PY_NARROW_UNICODE:
                        escape_unicode(high_surrogate_from_unicode_scalar(ch), ptr)
                        ptr += 6
                        escape_unicode(low_surrogate_from_unicode_scalar(ch), ptr)
                        ptr += 6
                    else:
                        escape_unicode(ch, ptr)
                        ptr += 6
                else:
                    ptr[0] = ch
                    ptr += 1

            curr += 1

        ptr[0] = c'"'

        return new_length + 2

    cdef inline Py_ssize_t write_unquoted_string(self, unicode string) except -1:
        cdef:
            const char *s = PyUnicode_AS_DATA(string)
            Py_ssize_t length = PyUnicode_GET_SIZE(string)
            array.array dest = self.dest

        array.extend_buffer(dest, <char*>s, length)
        return length


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

    cdef Py_ssize_t write_short_float_repr(self, object py_float) except -1:
        cdef:
            array.array dest = self.dest
            unicode string = f"{py_float:.{self.float_precision}f}"
            const Py_UNICODE *s = PyUnicode_AS_UNICODE(string)
            Py_ssize_t length = PyUnicode_GET_SIZE(string)
            Py_UNICODE ch

        # read digits backwards, skipping all the '0's until either a
        # non-'0' or '.' is found
        while length > 0:
            ch = s[length-1]
            if ch == c'.':
                length -= 1  # skip the trailing dot
                break
            elif ch != c'0':
                break
            length -= 1

        array.extend_buffer(dest, <char*>s, length)
        return length