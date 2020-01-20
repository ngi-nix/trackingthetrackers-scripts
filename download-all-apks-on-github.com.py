#!/usr/bin/env python3

import os
import requests
import time
from datetime import datetime
from github import Github, GithubException

def download_file(url):
    local_filename = url.replace('https://', '')
    print(url, '-->', local_filename)
    if os.path.exists(local_filename):
        return
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    with requests.get(url, stream=True) as r:
        try:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
        except requests.exceptions.HTTPError as e:
            print(e)

def check_rate_limit(g, msg=None):
    # standard rate limit is 5000 requests per hour
    remaining, limit = g.rate_limiting
    if remaining < 10:
        print('\nhit rate limit (%d per hour), waiting until %s'
              % (limit,
                 datetime.utcfromtimestamp(g.rate_limiting_resettime).strftime("%A, %d. %B %Y %H:%m UTC")))
        now = int(datetime.utcnow().timestamp())
        if msg:
            print('\n', msg)
        time.sleep(g.rate_limiting_resettime - now + 1)


token = os.getenv('GITHUB_TOKEN')
g = Github(token)

check_rate_limit(g)

# TODO parse index-v1.jar and fetch all github projects there, then dl all those APKs

#for repo in g.search_repositories('android'):
for repo in g.get_repos():
    check_rate_limit(g, repo.full_name)
    print('.', end='', flush=True)
    if os.path.exists(os.path.join('github.com', repo.full_name)):
        continue
    try:
        for release in repo.get_releases():
            for asset in release.get_assets():
                if asset.browser_download_url.endswith('.apk'):
                    download_file(asset.browser_download_url)
    except GithubException:
        continue
    except requests.exceptions.ReadTimeout as e:
        print(e)
        time.sleep(600)
        continue
