from __future__ import absolute_import, unicode_literals
import openstep_plist
from openstep_plist.writer import Encoder
import pytest


def test_Encoder_cinit():
    e = Encoder()
    assert len(e.buf) == 0
