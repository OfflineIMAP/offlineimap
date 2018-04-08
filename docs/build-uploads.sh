#!/bin/sh
#
# vim: expandtab ts=2 :

WEBSITE_UPLOADS='./website/_uploads'

while true
do
  test -d .git && break
  cd ..
done

set -e

echo "make clean"
make clean >/dev/null
echo "make targz"
make targz >/dev/null

# Defined in the root Makefile.
version="$(./offlineimap.py --version)"
abbrev="$(git log --format='%h' HEAD~1..)"
targz="../offlineimap-v${version}-${abbrev}.tar.gz"

filename="offlineimap-v${version}.tar.gz"

mv -v "$targz" "${WEBSITE_UPLOADS}/${filename}"
cd "$WEBSITE_UPLOADS"
for digest in sha1 sha256 sha512
do
  target="${filename}.${digest}"
  echo "Adding digest ${WEBSITE_UPLOADS}/${target}"
  "${digest}sum" "$filename" > "$target"
done
