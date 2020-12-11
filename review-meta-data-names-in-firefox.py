#!/usr/bin/env python3
#
# This script gets the tracker company names from Exodus, the searches
# through the names extracted from <meta-data> items in our APK set.
# It then opens firefox with searches by the exact names from
# <meta-data> to find which company those names belong to.

import json, os, re, requests

tracker_names = set()
r = requests.get('https://etip.exodus-privacy.eu.org/trackers/export')
r.raise_for_status()
for tracker in r.json()['trackers']:
    for name in re.sub(r'[^A-Za-z0-9-]', r' ', tracker['name']).split():
        tracker_names.add(name.lower())

for k in [
        'act',
        'ad',
        'add',
        'ads',
        'an',
        'and',
        'app',
        'by',
        'channel',
        'core',
        'data',
        'digital',
        'in',
        'map',
        'max',
        'mobile',
        'open',
        'push',
        'ru',
        'sdk',
        'service',
        'tr',
]:
    tracker_names.remove(k)
for name in sorted(tracker_names):
    if len(name) < 2:
        tracker_names.remove(name)

if not os.path.exists('search_space.json'):
    os.system('wget https://gitlab.com/trackingthetrackers/trackers-clean-feature-vectors/-/raw/master/search_space.json')
with open('search_space.json') as fp:
    data = json.load(fp)

print(len(data['apks'][0]['metaDataNames']))
reviewed = set()
if os.path.exists('reviewed.json'):
    with open('reviewed.json') as fp:
        reviewed = set(json.load(fp))

i = 0
display = set()
print('looking for %s names:' % len(tracker_names))
for name in sorted(tracker_names):
    if name in reviewed:
        continue
    print('-----------------------------------------------')
    print(name)
    reviewed.add(name)
    opened_etip = False
    for metadataname in sorted(data['apks'][0]['metaDataNames']):
        if name in metadataname.lower():
            display.add(metadataname)
            if not opened_etip:
                os.system('firejail --quiet firefox "https://etip.exodus-privacy.eu.org/admin/trackers/tracker/?q='
                          + name + '"')
                opened_etip = True
            os.system('firejail --quiet firefox "https://duckduckgo.com/?q=%22' + metadataname + '%22"')
            i += 1
    if i > 20:
        break

with open('reviewed.json', 'w') as fp:
    json.dump(sorted(reviewed), fp)
print(i, sorted(display))
