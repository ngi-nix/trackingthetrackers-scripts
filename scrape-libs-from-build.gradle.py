#!/usr/bin/env python3

import json
import os
import re
import shutil

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, datetime):
            return obj.timestamp()
        return super().default(obj)

libline_path = re.compile(r'''.*(implementation|api|compile)\s+['"](\S+)['"].*''')
dictfile = os.path.basename(__file__) + '.dict.json'
output = None
if os.path.exists(dictfile):
    with open(dictfile) as fp:
        output = json.load(fp)
        if 'set' in output:
            output['set'] = set(output['set'])
if output is None:
    output = dict()
if output.get('set') is None:
    output['set'] = set()

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.gradle'):
            current_file = os.path.join(root, f)
            if current_file in output:
                continue
            output[current_file] = []
            with open(current_file) as fp:
                for m in libline_path.finditer(fp.read()):
                    print(m.group(2))
                    gradle_line = m.group(2)
                    output['set'].add(gradle_line)
                    # add another dict layer using appid, then current_file
                    output[current_file].append(gradle_line)
            if current_file in output and not output[current_file]:
                del(output[current_file])

    if os.path.exists(dictfile):
        shutil.move(dictfile, dictfile + '~')
    with open(dictfile, 'w') as fp:
        json.dump(output, fp, cls=Encoder)
