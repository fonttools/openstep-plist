# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import openstep_plist
from openstep_plist.writer import Writer
from openstep_plist._test import is_narrow_unicode
from io import StringIO
import sys
import pytest


class TestWriter(object):
    def test_simple(self):
        w = Writer()
        assert w.write("abc") == 3
        assert w.getvalue() == "abc"

        f = StringIO()
        w.dump(f)
        assert f.getvalue() == "abc"

    def test_None(self):
        w = Writer()
        w.write(None)
        assert w.getvalue() == '"(nil)"'

    def test_unquoted_string(self):
        w = Writer()
        assert w.write(".appVersion") == 11
        assert w.getvalue() == ".appVersion"

    @pytest.mark.parametrize(
        "string, expected",
        [
            ("", '""'),
            ("\n\t\r", '"\n\t\r"'),
            ("\a\b\v\f", '"\\a\\b\\v\\f"'),
            ("\\", '"\\\\"'),
            ('"', '"\\""'),
            ("\0\1\2\3\4\5\6", '"\\000\\001\\002\\003\\004\\005\\006"'),
            ("\x0E\x0F\x10\x11\x12\x13", '"\\016\\017\\020\\021\\022\\023"'),
            ("\x14\x15\x16\x17\x18\x19", '"\\024\\025\\026\\027\\030\\031"'),
            ("\x1a\x1b\x1c\x1d\x1e\x1f\x7f", '"\\032\\033\\034\\035\\036\\037\\177"'),
            ("\x80\x81\x9E\x9F\xA0", '"\\U0080\\U0081\\U009E\\U009F\\U00A0"'),
            ("\U0001F4A9", '"\\UD83D\\UDCA9"'),  # '💩'
            # if string starts with digit, always quote it to distinguish from number
            ("1", '"1"'),
            ("1.1", '"1.1"'),
            ("1zzz", '"1zzz"'),  # ... even if it's not actually a number
        ],
    )
    def test_quoted_string(self, string, expected):
        w = Writer()
        w.write(string)
        assert w.getvalue() == expected

    def test_quoted_string_no_unicode_escape(self):
        w = Writer(unicode_escape=False)
        w.write("\u0410") == 3
        assert w.getvalue() == '"\u0410"'

        w = Writer(unicode_escape=False)
        assert w.write("\U0001F4A9") == (4 if is_narrow_unicode() else 3)
        assert w.getvalue() == '"\U0001F4A9"'

    @pytest.mark.parametrize(
        "integer, expected",
        [
            (0, "0"),
            (1, "1"),
            (123, "123"),
            (0x7fffffffffffffff, "9223372036854775807"),
            (0x7fffffffffffffff + 1, "9223372036854775808"),
        ],
    )
    def test_int(self, integer, expected):
        w = Writer()
        w.write(integer)
        assert w.getvalue() == expected

    @pytest.mark.parametrize(
        "flt, expected",
        [
            (0.0, "0"),
            (1.0, "1"),
            (123.456, "123.456"),
            (0.01, "0.01"),
            (0.001, "0.001"),
            (0.0001, "0.0001"),
            (0.00001, "0.00001"),
            (0.000001, "0.000001"),
            (0.0000001, "0"),  # default precision is 6
        ],
    )
    def test_float(self, flt, expected):
        w = Writer()
        w.write(flt)
        assert w.getvalue() == expected

    def test_float_precision(self):
        w = Writer(float_precision=3)
        w.write(0.0001)
        assert w.getvalue() == "0"

        w = Writer(float_precision=0)
        w.write(0.999)
        assert w.getvalue() == "1"

    @pytest.mark.parametrize(
        "data, expected",
        [
            (b"\x00", "<00>"),
            (b"\x00\x01", "<0001>"),
            (b"\x00\x01\x02", "<000102>"),
            (b"\x00\x01\x02\x03", "<00010203>"),
            (b"\x00\x01\x02\x03\x04", "<00010203 04>"),
            (b"\x00\x01\x02\x03\x04\x05", "<00010203 0405>"),
            (b"\x00\x01\x02\x03\x04\x05\x06", "<00010203 040506>"),
            (b"\x00\x01\x02\x03\x04\x05\x06\x07", "<00010203 04050607>"),
            (b"\x00\x01\x02\x03\x04\x05\x06\x07\x08", "<00010203 04050607 08>"),
            (b"\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11", "<090A0B0C 0D0E0F10 11>"),
        ],
        ids=lambda p: p.decode() if isinstance(p, bytes) else p,
    )
    def test_data(self, data, expected):
        w = Writer()
        assert w.write(data) == len(expected)
        assert w.getvalue() == expected

    @pytest.mark.parametrize(
        "array, expected",
        [
            ([1], "(1)"),
            ([1, 2], "(1, 2)"),
            ([1.2, 3.4, 5.6], "(1.2, 3.4, 5.6)"),
            ((1, "a", ("b", 2)), "(1, a, (b, 2))"),
            ([b"a", b"b"], "(<61>, <62>)"),
            ([{"a": "b"}, {"c": "d"}], "({a = b;}, {c = d;})"),
        ],
    )
    def test_array(self, array, expected):
        w = Writer()
        assert w.write(array) == len(expected)
        assert w.getvalue() == expected

    @pytest.mark.parametrize(
        "dictionary, expected",
        [
            ({"a": "b"}, "{a = b;}"),
            ({1: "c"}, '{"1" = c;}'),
            (
                {"hello world": 12, "abc": [34, 56.8]},
                '{abc = (34, 56.8); "hello world" = 12;}',
            ),
        ],
    )
    def test_dictionary(self, dictionary, expected):
        w = Writer()
        assert w.write(dictionary) == len(expected)
        assert w.getvalue() == expected

    def test_type_error(self):
        obj = object()
        w = Writer()
        with pytest.raises(TypeError, match="not PLIST serializable"):
            w.write(obj)


def test_dumps():
    assert openstep_plist.dumps(
        {"a": 1, "b": 2.9999999, "c d": [33, 44], "e": (b"fghilmno", b"pqrstuvz")}
    ) == (
        '{a = 1; b = 3; "c d" = (33, 44); '
        "e = (<66676869 6C6D6E6F>, <70717273 7475767A>);}"
    )


def test_dump():
    fp = StringIO()
    openstep_plist.dump([1, b"2", {3: (4, "5")}], fp)
    assert fp.getvalue() == '(1, <32>, {"3" = (4, "5");})'
