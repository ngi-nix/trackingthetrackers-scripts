#!/bin/sh -ex
#
# this matches the SHA256 style of the androzoo lists

for f in ../az/*.apk; do
    apk=`sha256sum $f | awk '{print $1}' | tr '[:lower:]' [':upper:]'`.apk
    test -e $apk && continue
    ln -iv $f $apk
done
