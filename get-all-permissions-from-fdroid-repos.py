#!/usr/bin/env python3
#
# Get all permissions declared in all APKs in all known fdroid repos
# ./get-all-permissions-from-fdroid-repos.py > all-permissions-from-fdroid-repos.csv

import re
import requests
import sys
import urllib
from fdroidserver import common, index

config = dict()
config['jarsigner'] = 'jarsigner'
common.config = config
index.config = config

url_pat = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

r = requests.get('https://forum.f-droid.org/t/known-repositories/721')
r.raise_for_status()
urls = set()
urls.add('https://f-droid.org/repo')
urls.add('https://f-droid.org/archive')
for m in url_pat.finditer(r.text):
    if m:
        url = urllib.parse.urlparse(m.group())
        if url.path.strip('/').endswith('/repo'):
            urls.add(m.group())

uses_permissions_set = set()
for url in sorted(urls):
    print(url, file=sys.stderr)
    try:
        indexdata, etag = index.download_repo_index(url, verify_fingerprint=False)
        for appid, packages in indexdata['packages'].items():
            for package in packages:
                uses_permission = package.get('uses-permission')
                if uses_permission:
                    for p in uses_permission:
                        uses_permissions_set.add(p[0])
    except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
        print(e, file=sys.stderr)
for p in sorted(uses_permissions_set):
    print(p)
