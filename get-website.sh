#!/bin/zsh

if test -d website
then
	echo "Directory 'website' already exists..."
	exit 1
else
	git clone https://github.com/OfflineIMAP/offlineimap.github.io.git
cat <<EOF
Now, you can fork the website at https://github.com/OfflineIMAP/offlineimap.github.io
and add a reference to it:

  $ cd website
  $ git remote add myfork https://github.com/<username>/offlineimap.github.io.git
EOF
fi
