#!/bin/sh
#
# Licence: this file is in the public domain.
#
# Download and configure the repositories of the website or wiki.

repository=$1
github_remote=$2

#
# TODO
#
final_note () {
	cat <<EOF

Now, you can fork the repository into Github from $2
and add a reference to it in your local copy:

  <fork at Github>
  $ cd ./$1
  $ git remote add myfork https://github.com/<username>/.git
EOF
}

setup () {
	target_dir=$1
	remote_url=$2

	# Adjust $PWD if necessary.
	test -d scripts || cd ..
	if test ! -d scripts
	then
		echo "cannot figure the correct workdir..."
		exit 2
	fi

	if test -d $target_dir
	then
		echo "Directory '$target_dir' already exists..."
		exit 3
	fi

	git clone "${remote_url}.git" "$1"
	echo ''
	if test $? -gt 0
	then
		echo "Cannot fork $remote_url to $1"
		exit 4
	fi
}

configure_website () {
	renderer='./render.sh'

	echo "Found Github username: '$1'"
	echo "If it's wrong, please fix the script ./website/render.sh"

	cd ./website
	if test $? -eq 0
	then
		sed -r -i -e "s,{{USERNAME}},$1," "$renderer"
		cd ..
	else
		echo "ERROR: could not enter ./website. (?)"
	fi
}

configure_wiki () {
	:	# noop
}

test n$github_remote = 'n' && github_remote='origin'

# Get Github username.
#offlineimap_url="$(git config --local --get remote.origin.url)"
offlineimap_url="$(git config --local --get remote.nicolas33.url)"
username=$(echo $offlineimap_url | sed -r -e 's,.*github.com.([^/]+)/.*,\1,')


case n$repository in
	nwebsite)
		upstream=https://github.com/OfflineIMAP/offlineimap.github.io
		setup website "$upstream"
		configure_website "$username"
		final_note website "$upstream"
		;;
	nwiki)
		upstream=https://github.com/OfflineIMAP/offlineimap.wiki
		setup wiki "$upstream"
		configure_wiki
		final_note wiki "$upstream"
		;;
	*)
		cat <<EOF
Usage: ./get-repository.sh {website|wiki} [origin|<repository>]

<repository>: The name of the Git repository of YOUR fork at Github.
              Default: origin
EOF
		exit 1
		;;
esac

