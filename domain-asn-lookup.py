#! /usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Michael Pöhn <michael.poehn@fsfe.org>
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# standalone project:
# https://gitlab.com/uniqx/domain-asn-lookup

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


def lookup_newest_asn_db_version_rib(sess, url):
    resp = sess.get(url)
    matches = re.findall(r"href=\"(rib\.\d{8}\.\d{4}\.bz2)\"", resp.text)
    if not matches:
        raise Exception(f"could not find rib: {url}")
    matches.sort(reverse=True)
    url += matches[0]

    return url


def lookup_newest_asn_db_version(sess=requests.Session()):
    url = "http://archive.routeviews.org/route-views4/bgpdata/"
    resp = sess.get(url)
    matches = re.findall(r"href=\"([0-9]{4}\.[0-9]{2})\/\"", resp.text)
    if not matches:
        print("could not lookup newest ASN db version")
        sys.exit(1)
    matches.sort(reverse=True)

    for m in matches:
        u = url + m + "/RIBS/"
        try:
            return lookup_newest_asn_db_version_rib(sess, u)
        except:
            pass
    print("could not lookup newest ASN db version")
    sys.exit(1)


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
    cachedir = os.path.join(
        appdirs.user_cache_dir(), os.path.basename(__file__).replace(".py", "")
    )
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


def main():

    parser = argparse.ArgumentParser(
        description="Tool for creating additional ML-feature-sets for domain name-datasets."
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help=argparse.SUPPRESS
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


if __name__ == "__main__":
    main()
