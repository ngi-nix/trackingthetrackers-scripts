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
            print(current_file)
            segments = current_file.split('/')
            appid = segments[1]
            if appid not in output:
                output[appid] = dict()
            subpath = os.path.join(*segments[2:])
            if subpath in output[appid]:
                continue
            output[appid][subpath] = []
            with open(current_file) as fp:
                for m in libline_path.finditer(fp.read()):
                    gradle_line = m.group(2)
                    output['set'].add(gradle_line)
                    output[appid][subpath].append(gradle_line)
            if subpath in output[appid] and not output[appid][subpath]:
                del(output[appid][subpath])

    if os.path.exists(dictfile):
        shutil.move(dictfile, dictfile + '~')
    with open(dictfile, 'w') as fp:
        json.dump(output, fp, cls=Encoder)
