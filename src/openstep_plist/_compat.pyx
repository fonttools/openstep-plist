#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

from cpython.version cimport PY_MAJOR_VERSION


cdef inline unicode tounicode(s, encoding="ascii", errors="strict"):
    if type(s) is unicode:
        return <unicode>s
    elif PY_MAJOR_VERSION < 3 and isinstance(s, bytes):
        return (<bytes>s).decode(encoding, errors=errors)
    elif isinstance(s, unicode):
        return unicode(s)
    else:
        raise TypeError(f"Could not convert to unicode: {s!r}")


cdef inline object tostr(s, encoding="ascii", errors="strict"):
    if isinstance(s, bytes):
        return s if PY_MAJOR_VERSION < 3 else s.decode(encoding, errors=errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors=errors) if PY_MAJOR_VERSION < 3 else s
    else:
        raise TypeError(f"Could not convert to str: {s!r}")
