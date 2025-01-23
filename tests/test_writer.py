# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import openstep_plist
from openstep_plist.writer import Writer, string_needs_quotes
from io import StringIO, BytesIO
from collections import OrderedDict
from textwrap import dedent
import string
import random
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
            ("\t", '"\t"'),
            ("\n\a\b\v\f\r", '"\\n\\a\\b\\v\\f\\r"'),
            ("\\", '"\\\\"'),
            ('"', '"\\""'),
            ("\0\1\2\3\4\5\6", '"\\000\\001\\002\\003\\004\\005\\006"'),
            ("\x0E\x0F\x10\x11\x12\x13", '"\\016\\017\\020\\021\\022\\023"'),
            ("\x14\x15\x16\x17\x18\x19", '"\\024\\025\\026\\027\\030\\031"'),
            ("\x1a\x1b\x1c\x1d\x1e\x1f\x7f", '"\\032\\033\\034\\035\\036\\037\\177"'),
            ("\x80\x81\x9E\x9F\xA0", '"\\U0080\\U0081\\U009E\\U009F\\U00A0"'),
            ("\U0001F4A9", '"\\UD83D\\UDCA9"'),  # '💩'
            # if string may be confused with a number wrap it in quotes
            ("1", '"1"'),
            ("1.1", '"1.1"'),
            ("-23", '"-23"'),
            ("-23yyy", '"-23yyy"'),
            ("-", '"-"'),
            ("-a-", '"-a-"'),
        ],
    )
    def test_quoted_string(self, string, expected):
        w = Writer()
        w.write(string)
        assert w.getvalue() == expected

    def test_quoted_string_dont_escape_newlines(self):
        w = Writer(escape_newlines=False)
        w.write("a\n\n\nbc")
        assert w.getvalue() == '"a\n\n\nbc"'

    def test_quoted_string_no_unicode_escape(self):
        w = Writer(unicode_escape=False)
        w.write("\u0410") == 3
        assert w.getvalue() == '"\u0410"'

        w = Writer(unicode_escape=False)
        assert w.write("\U0001F4A9") == 3
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
        "data, expected, expected_no_spaces",
        [
            (b"\x00", "<00>", "<00>"),
            (b"\x00\x01", "<0001>", "<0001>"),
            (b"\x00\x01\x02", "<000102>", "<000102>"),
            (b"\x00\x01\x02\x03", "<00010203>", "<00010203>"),
            (b"\x00\x01\x02\x03\x04", "<00010203 04>", "<0001020304>"),
            (b"\x00\x01\x02\x03\x04\x05", "<00010203 0405>", "<000102030405>"),
            (b"\x00\x01\x02\x03\x04\x05\x06", "<00010203 040506>", "<00010203040506>"),
            (b"\x00\x01\x02\x03\x04\x05\x06\x07", "<00010203 04050607>", "<0001020304050607>"),
            (b"\x00\x01\x02\x03\x04\x05\x06\x07\x08", "<00010203 04050607 08>", "<000102030405060708>"),
            (b"\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11", "<090A0B0C 0D0E0F10 11>", "<090A0B0C0D0E0F1011>"),
        ],
        ids=lambda p: p.decode() if isinstance(p, bytes) else p,
    )
    def test_data(self, data, expected, expected_no_spaces):
        w = Writer()
        assert w.write(data) == len(expected)
        assert w.getvalue() == expected

        w = Writer(binary_spaces=True)
        assert w.write(data) == len(expected)
        assert w.getvalue() == expected

        w = Writer(binary_spaces=False)
        # assert w.write(data) == len(expected_no_spaces)
        w.write(data)
        assert w.getvalue() == expected_no_spaces

    def test_bool(self):
        w = Writer()
        assert w.write(True) == 1
        assert w.getvalue() == "1"

        w = Writer()
        assert w.write(False) == 1
        assert w.getvalue() == "0"

    @pytest.mark.parametrize(
        "array, expected_no_indent, expected_indent",
        [
            ([], "()", "()"),
            ((), "()", "()"),
            ([1], "(1)", "(\n  1\n)"),
            ([1, 2], "(1, 2)", "(\n  1,\n  2\n)"),
            ([1.2, 3.4, 5.6], "(1.2, 3.4, 5.6)", "(\n  1.2,\n  3.4,\n  5.6\n)"),
            (
                (1, "a", ("b", 2)),
                "(1, a, (b, 2))",
                "(\n  1,\n  a,\n  (\n    b,\n    2\n  )\n)",
            ),
            ([b"a", b"b"], "(<61>, <62>)", "(\n  <61>,\n  <62>\n)"),
            (
                [{"a": "b"}, {"c": "d"}],
                "({a = b;}, {c = d;})",
                "(\n  {\n    a = b;\n  },\n  {\n    c = d;\n  }\n)",
            ),
        ],
    )
    def test_array(self, array, expected_no_indent, expected_indent):
        w = Writer()
        assert w.write(array) == len(expected_no_indent)
        assert w.getvalue() == expected_no_indent

        w = Writer(indent=2)
        assert w.write(array) == len(expected_indent)
        assert w.getvalue() == expected_indent

    @pytest.mark.parametrize(
        "dictionary, expected_no_indent, expected_indent",
        [
            ({}, "{}", "{}"),
            (OrderedDict(), "{}", "{}"),
            ({"a": "b"}, "{a = b;}", "{\n  a = b;\n}"),
            ({1: "c"}, '{"1" = c;}', '{\n  "1" = c;\n}'),
            (
                {"hello world": 12, "abc": [34, 56.8]},
                '{abc = (34, 56.8); "hello world" = 12;}',
                '{\n  abc = (\n    34,\n    56.8\n  );\n  "hello world" = 12;\n}',
            ),
            (
                OrderedDict([("z", 2), ("a", 1), (12, "c")]),
                '{z = 2; a = 1; "12" = c;}',
                '{\n  z = 2;\n  a = 1;\n  "12" = c;\n}',
            ),
        ],
    )
    def test_dictionary(self, dictionary, expected_no_indent, expected_indent):
        w = Writer()
        assert w.write(dictionary) == len(expected_no_indent)
        assert w.getvalue() == expected_no_indent

        w = Writer(indent="  ")
        assert w.write(dictionary) == len(expected_indent)
        assert w.getvalue() == expected_indent

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
    assert openstep_plist.dumps(
        {
            "features": dedent(
                """\
                sub periodcentered by periodcentered.case;
                sub bullet by bullet.case;
                """
            ),
        },
        escape_newlines=False,
    ) == (
        '{features = "sub periodcentered by periodcentered.case;\n'
        'sub bullet by bullet.case;\n'
        '";}'
    )


def test_dump():
    plist = [1, b"2", {3: (4, "5\n6", "\U0001F4A9")}]
    fp = StringIO()
    openstep_plist.dump(plist, fp)
    assert fp.getvalue() == '(1, <32>, {"3" = (4, "5\\n6", "\\UD83D\\UDCA9");})'

    fp = BytesIO()
    openstep_plist.dump(plist, fp, unicode_escape=False)
    assert fp.getvalue() == b'(1, <32>, {"3" = (4, "5\\n6", "\xf0\x9f\x92\xa9");})'

    fp = BytesIO()
    openstep_plist.dump(plist, fp, escape_newlines=False, unicode_escape=False)
    assert fp.getvalue() == b'(1, <32>, {"3" = (4, "5\n6", "\xf0\x9f\x92\xa9");})'

    with pytest.raises(AttributeError):
        openstep_plist.dump(plist, object())


valid_unquoted_chars = (
    string.ascii_uppercase + string.ascii_lowercase + string.digits + "._$"
)
invalid_unquoted_chars = [
    chr(c) for c in range(128) if chr(c) not in valid_unquoted_chars
]


@pytest.mark.parametrize(
    "string, expected",
    [
        (string.ascii_uppercase, False),
        (string.ascii_lowercase, False),
        # digits are allowed unquoted if not in first position
        ("a" + string.digits, False),
        (".appVersion", False),
        ("_private", False),
        ("$PWD", False),
        ("1zzz", False),
        ("192.168.1.1", False),
        ("0", True),
        ("1", True),
        ("2", True),
        ("3", True),
        ("4", True),
        ("5", True),
        ("6", True),
        ("7", True),
        ("8", True),
        ("9", True),
        ("", True),
        ("-", True),
        ("A-Z", True),
        ("hello world", True),
        ("\\backslash", True),
        ("http://github.com", True),
        (random.choice(invalid_unquoted_chars), True),
    ],
)
def test_string_needs_quotes(string, expected):
    assert string_needs_quotes(string) is expected


def test_single_line_tuples():
    assert openstep_plist.dumps({"a": 1, "b": (2, 3), "c": "Hello"}, indent=0) == (
        """{
a = 1;
b = (
2,
3
);
c = Hello;
}"""
    )
    assert openstep_plist.dumps(
        {"a": 1, "b": (2, 3), "c": "Hello"}, indent=0, single_line_tuples=True
    ) == (
        """{
a = 1;
b = (2,3);
c = Hello;
}"""
    )


def test_sort_keys():
    plist = {"c": 1, "b": {"z": 9, "y": 8, "x": 7}, "a": "Hello"}
    sorted_result = "{a = Hello; b = {x = 7; y = 8; z = 9;}; c = 1;}"
    unsorted_result = "{c = 1; b = {z = 9; y = 8; x = 7;}; a = Hello;}"
    assert openstep_plist.dumps(plist) == sorted_result
    assert openstep_plist.dumps(plist, sort_keys=True) == sorted_result
    assert openstep_plist.dumps(plist, sort_keys=False) == unsorted_result


def test_single_line_empty_objects():
    plist = {"a": [], "b": {}, "c": [{}], "d": [[]], "e": {"f": {}, "g": []}}
    single_line_result = """{
a = ();
b = {};
c = (
{}
);
d = (
()
);
e = {
f = {};
g = ();
};
}"""
    multi_line_result = """{
a = (
);
b = {
};
c = (
{
}
);
d = (
(
)
);
e = {
f = {
};
g = (
);
};
}"""
    assert openstep_plist.dumps(plist, indent=0) == single_line_result
    assert openstep_plist.dumps(plist, indent=0, single_line_empty_objects=True) == single_line_result
    assert openstep_plist.dumps(plist, indent=0, single_line_empty_objects=False) == multi_line_result
