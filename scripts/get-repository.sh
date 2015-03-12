#!/bin/bash
#
# Licence: this file is in the public deomain.
#
# Download and configure the repositories of the website or wiki.

repository=$1
github_remote=$2

#
# TODO
#
function final_note () {
	cat <<EOF

Now, you can fork the repository into Github from $2
and add a reference to it in your local copy:

  <fork at Github>
  $ cd ./$1
  $ git remote add myfork https://github.com/<username>/.git
EOF
}

function setup () {
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

function write_renderer () {
	cat <<EOF
#!/bin/bash
#
# Licence: this file is in the public deomain.
#
# Render the website at $1 OfflineIMAP fork.

username=$1
remote=git@github.com:\${username}/offlineimap.git

function clean() {
	echo "Cleaning gh-pages from public fork $username at ${remote}..."
	git push "\$remote" :gh-pages && {
		echo "\nSuccessfully terminated!"
		exit 0
	}
	exit 1
}

if test "n\$username" = 'n'
then
	echo "Github username is not configured"
	exit 2
fi

git push \$remote HEAD:gh-pages && {
	echo "\nCurrent HEAD pushed to Github fork of offlineimap.git."
	echo "Visit http://${username}.github.io/offlineimap to see how it is rendered"
	echo "Press Ctrl+C once done"
}
EOF
}

function configure_website () {
	renderer='./render.sh'

	echo "Found Github username: '$1'"
	echo "If it's wrong, please fix the script ./website/render.sh"

	cd ./website
	if test $? -eq 0
	then
		write_renderer "$1" > "$renderer"
		chmod u+x "$renderer"
		cd ..
	else
		echo "ERROR: could not write renderer."
	fi
}

function configure_wiki () {
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

