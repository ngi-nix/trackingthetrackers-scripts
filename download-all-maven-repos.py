#!/usr/bin/env python3

import json
import os
import requests
import xmltodict

from bs4 import BeautifulSoup

extensions = ('.aar', '.asc', '.jar', '.md5', '.pom')

def opendirs(url):
    print('opendirs', url)
    r = requests.get(url, stream=True, allow_redirects=True)
    if r.status_code != 200:
        return
    _, extension = os.path.splitext(url)
    if extension in extensions:
        path = url.replace('https://', '').replace('http://', '')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print("DOWNLOADING", url, 'to', path)
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
    else:
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.find_all('a'):
            if a.string:
                opendirs(url + '/' + a.string)

repos = [
    "http://dl.bintray.com/countly/maven",
    "http://dl.bintray.com/kochava/maven",
    "http://dl.bintray.com/ironsource-mobile/android-sdk",
    "http://fyber.bintray.com/maven",
    "https://packagecloud.io/smartadserver/android/maven2",
    "http://hypertrack-android-sdk.s3-website-us-west-2.amazonaws.com",
    "https://maven.fabric.io/public",
    "http://kochava.bintray.com/maven",
    "http://maven.google.com",
]

#for repo in repos:
#    opendirs(repo)

with open('jcenter-urls.json') as fp:
    for url in sorted(json.load(fp)):
        opendirs(url)
