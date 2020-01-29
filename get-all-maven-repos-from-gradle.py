#!/usr/bin/env python3

import json
import os
import re
import pprint

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, datetime):
            return obj.timestamp()
        return super().default(obj)

url_pat = re.compile(b'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

output = dict()
urls = set()
output['urls'] = urls
for root, dirs, files in os.walk('.'):
    for f in files:
        if '.gradle' in f:
            current_file = os.path.join(root, f)
            segments = current_file.split('/')
            appid = segments[1]
            if len(segments) < 3:
                continue
            subpath = os.path.join(*segments[2:])
            gradle_file = os.path.join(root, f)
            with open(gradle_file, 'rb') as fp:
                for m in url_pat.finditer(fp.read()):
                    url = m.group().decode()
                    urls.add(url)
                    if appid not in output:
                        output[appid] = dict()
                    if subpath not in output[appid]:
                        output[appid][subpath] = []
                    output[appid][subpath].append(url)
            #os.system('/home/hans/code/jedisct1/ipgrep/ipgrep.py ' + gradle_file)

with open(os.path.basename(__file__ + '.json'), 'w') as fp:
    json.dump(output, fp, cls=Encoder)
