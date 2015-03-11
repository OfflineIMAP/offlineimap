#!/bin/zsh

if test -d wiki
then
	echo "Directory 'wiki' already exists..."
	exit 1
else
	git clone https://github.com/OfflineIMAP/offlineimap.wiki.git wiki
	cat <<EOF

The wiki stands in the './wiki' directory.

If you want to to pull requests, fork the wiki at Github from https://github.com/OfflineIMAP/offlineimap-wiki
Next, learn your local copy of the wiki that you have a fork:

  $ cd ./wiki
  $ git remote add myfork https://github.com/<username>/offlineimap-wiki.git

You can now push your WIPs with:

  $ git push myfork <ref>:<ref>
EOF
fi
