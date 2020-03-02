#!/bin/sh -e
#
# this matches the SHA256 style of the androzoo lists

for f in [A-F0-9]*.apk; do
    apk=`sha256sum $f | awk '{print $1}' | tr '[:lower:]' [':upper:]'`.apk
    if [ $apk != $f ]; then
	printf "\nERROR mismatch: $apk should have a checksum of `echo $f | sed 's,\.apk$,,'`\n"
    else
	printf '.'
    fi
done
