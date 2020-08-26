#! /usr/env/bin python3

# SPDX-FileCopyrightText: 2020 Michael Pöhn <michael.poehn@fsfe.org>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
import bz2
import re
import os
import sys
import time
import socket
import argparse
import fileinput
import datetime
import pathlib
import email.utils

import pyasn
import pyasn.mrtx
import appdirs
import requests


def lookup_newest_asn_db_version(sess=requests.Session()):
    url = "http://archive.routeviews.org/route-views4/bgpdata/"
    resp = sess.get(url)
    matches = re.findall(r"href=\"(\d{4}\.\d{2})/\"", resp.text)
    if not matches:
        print("could not lookup newest ASN db version")
        sys.exit(1)
    matches.sort(reverse=True)
    url += matches[0] + "/RIBS/"

    resp = sess.get(url)
    matches = re.findall(r"href=\"(rib\.\d{8}\.\d{4}\.bz2)\"", resp.text)
    if not matches:
        print("could not lookup newest ASN db version")
        sys.exit(1)
    matches.sort(reverse=True)
    url += matches[0]

    return url


def update_asn_database(dbpath):
    with requests.Session() as sess:
        newest_url = lookup_newest_asn_db_version(sess=sess)
        resp = sess.head(newest_url)
        latest_date = email.utils.parsedate_to_datetime(resp.headers["Last-Modified"])

        cache_date = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        if os.path.exists(dbpath):
            cache_date = datetime.datetime.fromtimestamp(
                pathlib.Path(dbpath).stat().st_mtime
            ).replace(tzinfo=datetime.timezone.utc)
        if latest_date > cache_date:
            # print("downloading newest ASN database (~100mb, might take a while) ... ", end="", flush=True)
            with sess.get(newest_url, stream=True) as r:
                with bz2.open(io.BytesIO(r.content)) as archive:
                    prefixes = pyasn.mrtx.parse_mrt_file(
                        archive, print_progress=False, skip_record_on_error=True
                    )
                    pyasn.mrtx.dump_prefixes_to_file(prefixes, dbpath)
            os.utime(
                dbpath,
                (
                    time.mktime(latest_date.timetuple()),
                    time.mktime(latest_date.timetuple()),
                ),
            )
            # print("complete")


def init_asn_cache():
    cachedir = os.path.join(appdirs.user_cache_dir(), "domain_feature_tool")
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
    dbpath = os.path.join(cachedir, "rib.bz2")
    update_asn_database(dbpath)

    return dbpath


def process(fp, dbpath):

    db = pyasn.pyasn(dbpath)

    for line in fp:
        for domain in line.strip().split():
            try:
                ip = socket.gethostbyname(domain)
                print(domain, db.lookup(ip)[0])
            except socket.gaierror:
                pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Tool for creating additional ML-feature-sets for domain name-datasets. Expects domain names in stdin or attempts to read them form a file if -f is specified"
    )
    parser.add_argument("-f", "--file", default=None)
    config = parser.parse_args()

    dbpath = init_asn_cache()

    if config.file:
        encoding = "utf-8"
        with open(config.file, "r", encoding=encoding) as f:
            process(f, dbpath)
    else:
        process(fileinput.input(), dbpath)
