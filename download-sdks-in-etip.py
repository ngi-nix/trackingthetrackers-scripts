#!/usr/bin/env python3

import json
import os
import requests
from urllib.parse import urlunsplit
import xml.etree.ElementTree as ElementTree


def download_file(url):
    filename = url.split('/')[-1]
    # the stream=True parameter keeps memory usage low
    r = requests.get(url, stream=True, allow_redirects=True,
                     headers={'User-Agent': 'F-Droid'})
    if r.status_code != 200:
        return
    filepath = os.path.join(*(url.split('/')[1:]))
    if os.path.exists(filepath):
        return filepath
    print(url)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as fp:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                fp.write(chunk)
                fp.flush()
    return filepath


# group ID segments separated by / with a mandatory trailing /
GROUP_ID_SLASH_URLS = [
    'https://jcenter.bintray.com/',
    'https://repo1.maven.org/maven2/',
]

data = None
if os.path.exists('trackers.json'):
    with open('trackers.json') as fp:
        data = json.load(fp)
else:
    r = requests.get('https://etip.exodus-privacy.eu.org/api/trackers/',
                     headers={
                         'Authorization': 'Token ' + os.getenv('ETIP_TOKEN'),
                         'User-Agent': 'F-Droid',
                     })
    r.raise_for_status()
    data = r.json()

for tracker in data:
    artifact_ids = [artifact_id.strip() for artifact_id in tracker.get('artifact_id', '').split('|')]
    if '' in artifact_ids:
        artifact_ids.remove('')
    if not artifact_ids:
        continue
    group_ids = [group_id.strip() for group_id in tracker.get('group_id', '').split('|')]
    if '' in group_ids:
        group_ids.remove('')
    if not group_ids:
        continue

    name = tracker['name'].strip().lower()
    maven_repositories = [maven_repository.strip() for maven_repository in tracker.get('maven_repository', '').split('|')]
    maven_repositories.append('https://dl.bintray.com/%s/maven/' % name)
    maven_repositories += GROUP_ID_SLASH_URLS
    if '' in maven_repositories:
        maven_repositories.remove('')

    for maven_repository in maven_repositories:
        for group_id in group_ids:
            for artifact_id in artifact_ids:
                path = os.path.join(*(group_id.split('.') + [artifact_id]))
                url = os.path.join(maven_repository, path)
                metadata = os.path.join(url, 'maven-metadata.xml')
                metadata_file = download_file(metadata)
                if metadata_file:
                    print(metadata_file)
                    with open(metadata_file) as fp:
                        root = ElementTree.fromstring(fp.read())
                    versions = []
                    for vg in root.find('versioning'):
                        for v in vg.iter('version'):
                            version = v.text
                            for ext in ('.aar', '.jar', '-javadoc.jar', '.pom', '-sources.jar'):
                                fileurl = os.path.join(url, version, artifact_id + '-' + version + ext)
                                download_file(fileurl)
                                download_file(fileurl + '.asc')
