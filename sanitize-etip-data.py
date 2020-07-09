#!/usr/bin/env python3

import json
import os
import re
import requests
import sys
from urllib.parse import urlunsplit

REGEX = re.compile(r'([^\\])\.')

data = None
if os.path.exists('trackers.json'):
    with open('trackers.json') as fp:
        data = json.load(fp)
else:
    r = requests.get(
        'https://etip.exodus-privacy.eu.org/api/trackers/',
        headers={
            'Authorization': 'Token ' + os.getenv('ETIP_TOKEN'),
            'User-Agent': 'F-Droid',
        },
    )
    r.raise_for_status()
    data = r.json()
    with open('trackers.json', 'w') as fp:
        json.dump(data, fp, indent=2, sort_keys=True)

for tracker in data:
    origcode = tracker.get('code_signature', '')
    if origcode == 'NC':
        os.system('firefox https://etip.exodus-privacy.eu.org/admin/trackers/tracker/%s/change/'
                  % tracker.get('id', ''))
    code_signatures = [
        code_signature.strip()
        for code_signature in origcode.split('|')
    ]
    if '' in code_signatures:
        code_signatures.remove('')

    orignetwork = tracker.get('network_signature', '')
    if orignetwork == 'NC':
        os.system('firefox https://etip.exodus-privacy.eu.org/admin/trackers/tracker/%s/change/'
                  % tracker.get('id', ''))
    network_signatures = [
        network_signature.strip()
        for network_signature in orignetwork.split('|')
    ]
    if '' in network_signatures:
        network_signatures.remove('')

    if not code_signatures and not network_signatures:
        continue

    sanitized_code_signatures = set()
    for code_signature in code_signatures:
        if '.' in code_signature and '\\' not in code_signature:
            sanitized_code_signatures.add(REGEX.sub(r'\1\\.', code_signature))
        else:
            sanitized_code_signatures.add(code_signature)

    sanitized_network_signatures = set()
    for network_signature in network_signatures:
        if '.' in network_signature and '\\' not in network_signature:
            sanitized_network_signatures.add(REGEX.sub(r'\1\\.', network_signature))
        else:
            sanitized_network_signatures.add(network_signature)
            
    print(tracker['name'])
    codeout = '|'.join(sorted(sanitized_code_signatures))
    if sanitized_code_signatures:
        if origcode != codeout:
            print('\t', tracker.get('code_signature', ''))
            print('\t', codeout)
    networkout = '|'.join(sorted(sanitized_network_signatures))
    if sanitized_network_signatures:
        if orignetwork != networkout:
            print('\t', tracker.get('network_signature', ''))
            print('\t', networkout)
    if origcode != codeout or orignetwork != networkout:
        os.system('firefox https://etip.exodus-privacy.eu.org/admin/trackers/tracker/%s/change/'
                  % tracker.get('id', ''))
        sys.exit(1)
