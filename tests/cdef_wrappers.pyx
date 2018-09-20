from aplist._aplist cimport (
    _text,
    ParseInfo,
    is_valid_unquoted_string_char as c_is_valid_unquoted_string_char,
)
from cpython.unicode cimport (
    PyUnicode_FromUnicode, PyUnicode_AS_UNICODE, PyUnicode_GET_SIZE,
)


cdef class ParseContext:

    cdef unicode s
    cdef ParseInfo pi
    cdef object dict_type

    @classmethod
    def fromstring(ParseContext cls, string, dict_type=dict):
        cdef ParseContext self = ParseContext.__new__(cls)
        self.s = _text(string)
        cdef Py_ssize_t length = PyUnicode_GET_SIZE(self.s)
        cdef Py_UNICODE* buf = PyUnicode_AS_UNICODE(self.s)
        self.dict_type = dict_type
        self.pi = ParseInfo(
            begin=buf,
            curr=buf,
            end=buf + length,
            dict_type=<void*>dict_type,
        )
        return self


def is_valid_unquoted_string_char(Py_UNICODE c):
    return c_is_valid_unquoted_string_char(c)
