from __future__ import absolute_import, unicode_literals
import openstep_plist
from openstep_plist.writer import Writer
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
        assert w.write("\U0001F4A9") == (3 if sys.maxunicode > 0xFFFF else 4)
        assert w.getvalue() == '"\U0001F4A9"'
