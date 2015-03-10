#!/bin/zsh

if test -d wiki
then
	echo "Directory 'wiki' already exists..."
	exit 1
else
	git clone https://github.com/OfflineIMAP/offlineimap.wiki.git wiki
	cat <<EOF
Now, you can fork the wiki at https://github.com/OfflineIMAP/offlineimap-wiki
and add a reference to it:

  $ cd wiki
  $ git remote add myfork https://github.com/<username>/offlineimap-wiki.git
EOF
fi
