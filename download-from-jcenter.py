#!/usr/bin/env python3

import json
import os

models = [
    'trackers.detectionrule',
    'reports.report',
    'reports.apk',
    'reports.certificate',
    'reports.permission',
    'trackers.tracker',
    'reports.dnsquery',
    'reports.httppayload',
    'reports.networkanalysis',
    'reports.httpanalysis',
    'reports.application',
]

with open('dump_20180430.json') as fp:
    data = json.load(fp)

signatures = set()
for e in data:
        code_signature = e['fields'].get('code_signature')
        if code_signature:
            if 'carnival' in code_signature:
                print("SIG", code_signature)
            for sig in code_signature.split('|'):
                signatures.add(sig.strip().strip('.').strip('/'))

jcenter_urls = []
search_further_urls = []
for sig in signatures:
    if not sig:
        continue
    jcenter_urls.append('http://jcenter.bintray.com/' + sig.replace('.', '/'))
    search_further_urls.append('https://www.google.com/search?btnI=&pws=0&gl=us&gws_rd=cr&q=' + sig + '%20sdk%20download')

with open('jcenter-urls.json', 'w') as fp:
    json.dump(jcenter_urls, fp, sort_keys=True, indent=4)

with open('search-further-urls.json', 'w') as fp:
    json.dump(search_further_urls, fp, sort_keys=True, indent=4)
