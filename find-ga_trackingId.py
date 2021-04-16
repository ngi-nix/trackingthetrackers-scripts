#!/usr/bin/env python3
#
# Scan the provided dirs for APKs, then search those APKs for the
# Google Firebase Analytics API Key Identifier.

import os
import sys
import yaml
import zipfile
from androguard.core.bytecodes.axml import AXMLPrinter

try:
    import defusedxml.ElementTree as XMLElementTree
except ImportError:
    import xml.etree.ElementTree as XMLElementTree  # nosec this is a fallback only


def dump(data, stream):
    yaml.safe_dump(sorted(data), stream, encoding='utf-8', indent=2, width=9999, allow_unicode=True)


if len(sys.argv) > 1:
    search_dirs = sys.argv[1:]
else:
    search_dirs = ['.']
print('search_dirs', search_dirs)

output = set()
errors = set()
with open(os.path.basename(__file__).replace('.py', '.yaml'), 'w') as outfp, open(
    os.path.basename(__file__).replace('.py', '-errors.yaml'), 'w'
) as errorsfp:
    for d in search_dirs:
        for root, dirs, files in os.walk(d):
            for f in files:
                path = os.path.join(root, f)
                try:
                    with zipfile.ZipFile(path) as apk:
                        for info in apk.infolist():
                            if info.file_size < 10:
                                continue
                            name = info.filename
                            if name.startswith('res/') and name.endswith('.xml'):
                                with apk.open(name) as binary_xml:
                                    axml = AXMLPrinter(binary_xml.read())
                                    resources = XMLElementTree.fromstring(axml.get_xml())
                                    for item in resources:
                                        if 'ga_trackingId' == item.get('name'):
                                            output.add((path, name, item.get('name')))
                                            dump(output, outfp)
                                            break
                except (zipfile.BadZipFile, AssertionError, TypeError, ValueError) as e:
                    errors.add((path, '', '', str(e)))
                    dump(errors, errorsfp)
                    pass
    dump(output, outfp)
    dump(errors, errorsfp)
