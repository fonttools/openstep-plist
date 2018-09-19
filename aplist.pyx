#cython: language_level=3, linetrace=True

from cpython.unicode cimport (
    PyUnicode_FromUnicode, PyUnicode_AS_UNICODE, PyUnicode_GET_SIZE
)
from libc.stdint cimport uint32_t
from cpython cimport array
import array


cdef class ParseError(Exception):
    pass


cdef uint32_t line_number_strings(ParseInfo *pi):
    # warning: doesn't have a good idea of Unicode line separators
    cdef const Py_UNICODE *p = pi.begin
    cdef uint32_t count = 1
    while p < pi.curr:
        if p[0] == c'\r':
            count += 1
            if (p + 1)[0] == c'\n':
                p += 1
        elif p[0] == c'\n':
            count += 1
        p += 1
    return count


cdef inline bint is_valid_unquoted_string_char(Py_UNICODE x):
    return (
        (x >= c'a' and x <= c'z') or
        (x >= c'A' and x <= c'Z') or
        (x >= c'0' and x <= c'9') or
        x == c'_' or
        x == c'$' or
        x == c'/' or
        x == c':' or
        x == c'.' or
        x == c'-'
    )


cdef bint advance_to_non_space(ParseInfo *pi):
    """Returns true if the advance found something before the end of the buffer,
    false otherwise.
    """
    cdef Py_UNICODE ch2, ch3
    while pi.curr < pi.end:
        ch2 = pi.curr[0]
        pi.curr += 1
        if ch2 >= 9 and ch2 <= 0x0d:
            # tab, newline, vt, form feed, carriage return
            continue
        if ch2 == c'/':
            if pi.curr >= pi.end:
                # whoops; back up and return
                pi.curr -= 1
                return True
            elif pi.curr[0] == c'/':
                pi.curr += 1
                while pi.curr < pi.end:
                    # go to end of // comment line
                    ch3 = pi.curr[0]
                    if ch3 == c'\n' or ch3 == c'\r' or ch3 == 0x2028 or ch3 == 0x2029:
                        break
                    pi.curr += 1
            elif pi.curr[0] == c'*':
                # handle C-style comments /* ... */
                pi.curr += 1
                while pi.curr < pi.end:
                    ch2 = pi.curr[0]
                    pi.curr += 1
                    if ch2 == c'*' and pi.curr < pi.end and pi.curr[0] == c'/':
                        pi.curr += 1  # advance pat the '/'
                        break
            else:
                pi.curr -= 1
                return True
        else:
            pi.curr -= 1
            return True

    return False


cdef array.array unicode_array_template = array.array('u', [])


cdef inline void extend_array(array.array a, const Py_UNICODE *buf, Py_ssize_t length):
    cdef Py_ssize_t i
    for i in range(length):
        a.append(buf[i])


cdef unicode parse_quoted_plist_string(ParseInfo *pi, Py_UNICODE quote):
    cdef array.array string = array.clone(unicode_array_template, 0, zero=False)
    cdef const Py_UNICODE *start_mark = pi.curr
    cdef const Py_UNICODE *mark = pi.curr
    cdef Py_UNICODE ch
    while pi.curr < pi.end:
        ch = pi.curr[0]
        if ch == quote:
            break
        elif ch == c'\\':
            extend_array(string, mark, pi.curr - mark)
            pi.curr += 1
            # ch = get_slashed_char(pi)
            string.append(ch)
        else:
            pi.curr += 1
    if pi.end <= pi.curr:
        raise ParseError(
            "Unterminated quoted string starting on line %d"
            % line_number_strings(pi)
        )
    if not string:
        extend_array(string, mark, pi.curr - mark)
    else:
        if mark != pi.curr:
            extend_array(string, mark, pi.curr - mark)
    # Advance past the quote character before returning
    pi.curr += 1

    return PyUnicode_FromUnicode(string.data.as_pyunicodes, len(string))


cdef unicode parse_unquoted_plist_string(ParseInfo *pi):
    cdef const Py_UNICODE *mark = pi.curr
    cdef Py_UNICODE ch
    cdef array.array string
    cdef Py_ssize_t length
    while pi.curr < pi.end:
        ch = pi.curr[0]
        if is_valid_unquoted_string_char(ch):
            pi.curr += 1
        else:
            break
    if pi.curr != mark:
        length = pi.curr - mark
        string = array.clone(unicode_array_template, 0, zero=False)
        extend_array(string, mark, length)
        return PyUnicode_FromUnicode(string.data.as_pyunicodes, length)
    raise ParseError("Unexpected EOF")


cdef object parse_plist_object(ParseInfo *pi, bint required):
    cdef Py_UNICODE ch
    cdef bint found_char = advance_to_non_space(pi)
    if not found_char:
        if required:
            raise ParseError("Unexpected EOF while parsing plist")
    ch = pi.curr[0]
    pi.curr += 1
    # if ch == c'{':
    #     return parse_plist_dict(pi)
    # elif ch == c'(':
    #     return parse_plist_array(pi)
    # elif ch == c'<':
    #     return parse_plist_data(pi)
    # elif ch == c'\'' or ch == c'"':
    if ch == c'\'' or ch == c'"':
        return parse_quoted_plist_string(pi, ch)
    elif is_valid_unquoted_string_char(ch):
        pi.curr -= 1
        return parse_unquoted_plist_string(pi)
    else:
        pi.curr -= 1  # must back off the character we just read
        if required:
            raise ParseError(
                "Unexpected character '0x%x' at line %d"
                % (<unsigned long>ch, line_number_strings(pi))
            )


cpdef object loads(string):
    if not isinstance(string, unicode):
        string = string.decode("utf-8")

    cdef unicode s = <unicode>string
    cdef Py_ssize_t length = PyUnicode_GET_SIZE(s)
    cdef Py_UNICODE* buf = PyUnicode_AS_UNICODE(s)

    cdef ParseInfo pi = ParseInfo(buf, buf, buf + length)

    cdef object result = None
    cdef bint found_char = advance_to_non_space(&pi)
    if not found_char:
        # a file consisting of only whitespace or empty is defined as an
        # empty dictionary
        result = {}
    else:
        result = parse_plist_object(&pi, required=True)

    return result


def main(args=None):
    if args is None:
        import sys

        args = sys.argv[1:]

    if not args:
        return 1

    s = args[0]
    print(loads(s))
