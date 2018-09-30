#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

import array
from cpython cimport array
from cpython.unicode cimport (
    PyUnicode_FromUnicode,
    PyUnicode_AS_UNICODE,
    PyUnicode_AS_DATA,
    PyUnicode_GET_SIZE,
    PyUnicode_AsUTF8String,
)
from cpython.bytes cimport PyBytes_GET_SIZE
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


cdef Py_UNICODE *HEX_MAP = [
    c'0', c'1', c'2', c'3', c'4', c'5', c'6', c'7',
    c'8', c'9', c'A', c'B', c'C', c'D', c'E', c'F',
]

cdef Py_UNICODE *ARRAY_SEP_NO_INDENT = [c',', c' ']
cdef Py_UNICODE *DICT_KEY_VALUE_SEP = [c' ', c'=', c' ']
cdef Py_UNICODE *DICT_ITEM_SEP_NO_INDENT = [c';', c' ']


cdef inline bint is_valid_unquoted_string(const Py_UNICODE *a, Py_ssize_t length):
    # if string starts with digit or with a '-', always write it within quotes
    # to distinguish it from an actual (signed) integer or float number, which
    # are always written without quotes
    cdef Py_UNICODE ch = a[0]
    if c'0' <= ch <= c'9' or ch == c'-':
        return False

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
        cdef unicode s = self._getvalue()
        # figure out whether file object expects bytes or unicodes
        try:
            file.write(b"")
        except TypeError:
            file.write("")  # this better not fail...
            # file already accepts unicodes; use it directly
            file.write(s)
        else:
            # file expects bytes; always encode as UTF-8
            file.write(PyUnicode_AsUTF8String(s))

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
        elif isinstance(obj, list):
            return self.write_array_from_list(obj)
        elif isinstance(obj, tuple):
            return self.write_array_from_tuple(obj)
        elif isinstance(obj, dict):
            return self.write_dict(obj)
        elif isinstance(obj, bytes):
            return self.write_data(obj)
        else:
            raise TypeError(
                f"Object of type {type(obj).__name__} is not PLIST serializable"
            )

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

    cdef Py_ssize_t write_data(self, bytes data) except -1:
        cdef:
            array.array dest = self.dest
            const unsigned char *src = data
            Py_UNICODE *ptr
            Py_ssize_t length = PyBytes_GET_SIZE(data)
            Py_ssize_t extra_length, i, j

        # the number includes the opening '<' and closing '>', and the
        # interleaving spaces between each group of 4 bytes; each byte
        # is encoded with two hexadecimal digit
        extra_length = 2 + 2*length + ((length - 1)//4 if length > 4 else 0)

        j = Py_SIZE(dest)
        array.resize_smart(dest, j + extra_length)
        ptr = dest.data.as_pyunicodes

        ptr[j] = c'<'
        j += 1
        for i in range(length):
            ptr[j] = HEX_MAP[(src[i] >> 4) & 0x0F]
            j += 1
            ptr[j] = HEX_MAP[src[i] & 0x0F]
            if (i & 3) == 3 and i < length - 1:
                # if we've just finished a 32-bit int, print a space
                j += 1
                ptr[j] = c' '
            j += 1
        ptr[j] = c'>'

        return extra_length

    # XXX The two write_array_* methods are identical apart from the type of
    # the 'seq' (one is list, the other is tuple). I tried using fused type
    # ``'list_or_tuple' to avoid duplication but I couldn't make it work...

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef Py_ssize_t write_array_from_list(self, list seq) except -1:
        cdef:
            Py_ssize_t length = len(seq)
            Py_ssize_t last = length - 1
            Py_ssize_t count
            Py_ssize_t i
            array.array dest = self.dest

        dest.append("(")
        count = 1

        for i in range(length):
            count += self.write_object(seq[i])
            if i != last:
                array.extend_buffer(dest, <char*>ARRAY_SEP_NO_INDENT, 2)
                count += 2

        dest.append(")")
        count += 1

        return count

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef Py_ssize_t write_array_from_tuple(self, tuple seq) except -1:
        cdef:
            Py_ssize_t length = len(seq)
            Py_ssize_t last = length - 1
            Py_ssize_t count
            Py_ssize_t i
            array.array dest = self.dest

        dest.append("(")
        count = 1

        for i in range(length):
            count += self.write_object(seq[i])
            if i != last:
                array.extend_buffer(dest, <char*>ARRAY_SEP_NO_INDENT, 2)
                count += 2

        dest.append(")")
        count += 1

        return count

    cdef Py_ssize_t write_dict(self, dict d) except -1:
        cdef:
            array.array dest = self.dest
            Py_ssize_t last = len(d) - 1
            Py_ssize_t count

        dest.append("{")
        count = 1

        for i, (key, value) in enumerate(sorted(d.items())):
            if not isinstance(key, unicode):
                key = unicode(key)
            count += self.write_string(key)

            array.extend_buffer(dest, <char*>DICT_KEY_VALUE_SEP, 3)
            count += 3

            count += self.write_object(value)

            if i != last:
                array.extend_buffer(dest, <char*>DICT_ITEM_SEP_NO_INDENT, 2)
                count += 2
            else:
                dest.append(";")
                count += 1

        dest.append("}")
        count += 1

        return count


def dumps(obj, bint unicode_escape=True, int float_precision=6):
    w = Writer(unicode_escape=unicode_escape, float_precision=float_precision)
    w.write(obj)
    return w.getvalue()


def dump(obj, fp, bint unicode_escape=True, int float_precision=6):
    w = Writer(unicode_escape=unicode_escape, float_precision=float_precision)
    w.write(obj)
    w.dump(fp)
