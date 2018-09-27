#cython: language_level=3
#distutils: define_macros=CYTHON_TRACE_NOGIL=1

from cpython.version cimport PY_MAJOR_VERSION
from cpython cimport array
import array


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


# must convert array type code to native str type else when using
# unicode literals on py27 one gets 'TypeError: must be char, not unicode'
cdef array.array unicode_array_template = array.array(tostr('u'), [])
