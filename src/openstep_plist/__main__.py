#!/usr/bin/env python

import openstep_plist
import json
import base64
import binascii
# from collections import OrderedDict


class BytesEncoder(json.JSONEncoder):

    def default(self, obj):
        from glyphsLib.types import BinaryData

        if isinstance(obj, (bytes, BinaryData)):
            return "<%s>" % binascii.hexlify(obj).decode()
        return json.JSONEncoder.default(self, obj)


def main(args=None):
    if args is None:
        import sys

        args = sys.argv[1:]

    if len(args) < 2:
        return 1

    method = args[0]
    if method == "-a":
        parse = openstep_plist.load
    elif method == "-g":

        def parse(fp, dict_type=dict):
            from glyphsLib.parser import Parser

            s = fp.read()
            p = Parser(current_type=dict_type)
            return p.parse(s)
    else:
        sys.exit("error: unknown option: %s" % method)

    infile = args[1]

    with open(infile, "r", encoding="utf-8") as fp:
        # data = parse(fp, dict_type=OrderedDict)
        data = parse(fp)

    if len(args) > 2:
        outfile = args[2]
        with open(outfile, "w", encoding="utf-8") as fp:
            json.dump(data, fp, cls=BytesEncoder, sort_keys=True, indent="  ")


if __name__ == "__main__":
    main()
