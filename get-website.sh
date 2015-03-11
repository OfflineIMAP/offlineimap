#!/bin/zsh

if test -d website
then
	echo "Directory 'website' already exists..."
	exit 1
else
	git clone https://github.com/OfflineIMAP/offlineimap.github.io.git website
	cat <<EOF

The website stands in the './website' directory.

If you want to to pull requests, fork the website at Github from https://github.com/OfflineIMAP/offlineimap.github.io
Next, learn your local copy of the website that you have a fork:

  $ cd ./website
  $ git remote add myfork https://github.com/<username>/offlineimap.github.io.git

You can now push your WIPs with:

  $ git push myfork <ref>:<ref>
EOF
fi
