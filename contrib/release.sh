#!/bin/sh
#
# Put into Public Domain, by Nicolas Sebrecht
#
# Create new releases in OfflineIMAP.

# TODO: https://developer.github.com/v3/repos/releases/#create-a-release
# https://developer.github.com/libraries/
# https://github.com/turnkeylinux/octohub
# https://github.com/michaelliao/githubpy (onefile)
# https://github.com/sigmavirus24/github3.py
# https://github.com/copitux/python-github3
# https://github.com/PyGithub/PyGithub
# https://github.com/micha/resty (curl)

# TODO: move configuration out and source it.
# TODO: implement rollback.

__VERSION__='v0.3'

SPHINXBUILD=sphinx-build

MAILING_LIST='offlineimap-project@lists.alioth.debian.org'

DOCSDIR='docs'
ANNOUNCE_MAGIC='#### Notes '
CHANGELOG_MAGIC='{:toc}'
CHANGELOG='Changelog.md'
CACHEDIR='.git/offlineimap-release'
WEBSITE='website'
WEBSITE_LATEST="${WEBSITE}/_data/latest.yml"

TMP_CHANGELOG_EXCERPT="${CACHEDIR}/changelog.excerpt.md"
TMP_CHANGELOG_EXCERPT_OLD="${TMP_CHANGELOG_EXCERPT}.old"
TMP_CHANGELOG="${CACHEDIR}/changelog.md"
TMP_ANNOUNCE="${CACHEDIR}/announce.txt"

True=0
False=1
Yes=$True
No=$False

DEBUG=$True

#
# $1: EXIT_CODE
# $2..: message
function die () {
  n=$1
  shift
  echo $*
  exit $n
}


function debug () {
  if test $DEBUG -eq $True
  then
    echo "DEBUG: $*" >&2
  fi
}



#
# $1: question
# $2: message on abort
#
function ask () {
  echo
  echo -n "--- $1 "
  read -r ans
  test "n$ans" = 'n' -o "n$ans" = 'ny' && return $Yes
  test "n$ans" = "ns" -o "n$ans" = 'nn' && return $No
  die 1 "! $2"
}



#
# $1: message
# $1: path to file
#
function edit_file () {
  ask "Press Enter to $1"
  test $? -eq $Yes && {
    $EDITOR "$2"
    reset
  }
}



function fix_pwd () {
  debug 'in fix_pwd'
  cd "$(git rev-parse --show-toplevel)" || \
    die 2 "cannot determine the root of the repository"
}


function prepare_env () {
  debug 'in prepare_env'
  mkdir "$CACHEDIR" 2>/dev/null
  test ! -d "$CACHEDIR" && die 5 "Could not make cache directory $CACHEDIR"
}


function check_dirty () {
  debug 'in check_dirty'
  git diff --quiet 2>/dev/null && git diff --quiet --cached 2>/dev/null || {
    die 4 "Commit all your changes first!"
  }
}


function welcome () {
  debug 'in welcome'
cat <<EOF
You will be prompted to answer questions.
Answer by:
- 'y'       : yes, continue (default)
- '<Enter>' : yes, continue
- 'n'       : no
- 's'       : skip (ONLY where applicable, otherwise continue)

Any other key will abort the program.
EOF
  ask 'Ready?'
}


function checkout_next () {
  debug 'in checkout_next'
  git checkout --quiet next || {
    die 6 "Could not checkout 'next' branch"
  }
}


function get_version () {
  debug 'in get_version'
  echo "v$(./offlineimap.py --version)"
}


function update_offlineimap_version () {
  debug 'in update_offlineimap_version'
  edit_file 'update the version in __init__.py' offlineimap/__init__.py
}


#
# $1: previous version
#
function get_git_history () {
  debug 'in get_git_history'
  git log --format='- %h %s. [%aN]' --no-merges  "${1}.."
}


#
# $1: previous version
#
function get_git_who () {
  debug 'in get_git_who'
  echo
  git shortlog --no-merges -sn "${1}.." | \
          sed -r -e 's, +([0-9]+)\t(.*),- \2 (\1),'
}



#
# $1: new version
# $2: shortlog
function changelog_template () {
  debug 'in changelog_template'
  cat <<EOF
// vim: expandtab ts=2 syntax=markdown

// WARNING: let at least one empy line before the real content.
//
// Write a new Changelog entry.
//
// Comments MUST start at the beginning of the lile with two slashes.
// They will by be ignored by the template engine.
//
### OfflineIMAP $1 ($(date +%Y-%m-%d))

#### Notes

// Add some notes. Good notes are about what was done in this release from the
// bigger perspective.
// HINT: explain most important changes.

#### Authors

The authors of this release.

// Use list syntax with '- '

#### Features

// Use list syntax with '- '

#### Fixes

// Use list syntax with '- '

#### Changes

// Use list syntax with '- '

// The preformatted log was added below. Make use of this to fill the sections
// above.

EOF
}



#
# $1: new version
# $2: previous version
#
function update_changelog () {
  debug 'in update_changelog'

  # Write Changelog excerpt.
  if test ! -f "$TMP_CHANGELOG_EXCERPT"
  then
    changelog_template "$1" > "$TMP_CHANGELOG_EXCERPT"
    get_git_history "$2" >> "$TMP_CHANGELOG_EXCERPT"
    get_git_who "$2" >> "$TMP_CHANGELOG_EXCERPT"
    edit_file "the Changelog excerpt" $TMP_CHANGELOG_EXCERPT

    # Remove comments.
    grep -v '//' "$TMP_CHANGELOG_EXCERPT" > "${TMP_CHANGELOG_EXCERPT}.nocomment"
    mv -f "${TMP_CHANGELOG_EXCERPT}.nocomment" "$TMP_CHANGELOG_EXCERPT"
  fi

  # Write new Changelog.
  cat "$CHANGELOG" > "$TMP_CHANGELOG"
  debug "include excerpt $TMP_CHANGELOG_EXCERPT to $TMP_CHANGELOG"
  sed -i -e "/${CHANGELOG_MAGIC}/ r ${TMP_CHANGELOG_EXCERPT}" "$TMP_CHANGELOG"
  debug 'remove trailing whitespaces'
  sed -i -r -e 's, +$,,' "$TMP_CHANGELOG"   # Remove trailing whitespaces.
  debug "copy to $TMP_CHANGELOG -> $CHANGELOG"
  cp -f "$TMP_CHANGELOG" "$CHANGELOG"

  # Check and edit Changelog.
  ask "Next step: you'll be asked to review the diff of $CHANGELOG"
  while true
  do
    git diff -- "$CHANGELOG" | less
    ask 'edit Changelog?' $CHANGELOG
    test ! $? -eq $Yes && break
    # Asked to edit the Changelog; will loop again.
    $EDITOR "$CHANGELOG"
  done
}


#
# $1: new version
#
function git_release () {
  debug 'in git_release'
  git commit -as -m"$1"
  git tag -a "$1" -m"$1"
  git checkout master
  git merge next
  git checkout next
}



function get_last_rc () {
  git tag | grep -E '^v([0-9][\.-]){3}rc' | sort -n | tail -n1
}

function get_last_stable () {
  git tag | grep -E '^v([0-9][\.])+' | grep -v '\-rc' | sort -n | tail -n1
}

function update_website_releases_info() {
  cat > "$WEBSITE_LATEST" <<EOF
# DO NOT EDIT MANUALLY: it is generated by a script (release.sh)
stable: $(get_last_stable)
rc: $(get_last_rc)
EOF
}


#
# $1: new version
#
function update_website () {
  debug 'in update_website'

  ask "update API of the website? (require $SPHINXBUILD)"
  if test $? -eq $Yes
  then
    # Check sphinx is available.
    $SPHINXBUILD --version > /dev/null 2>&1
    if test ! $? -eq 0
    then
      echo "Oops! you don't have $SPHINXBUILD installed?"
      echo "Cannot update the webite documentation..."
      echo "You should install it and run:"
      echo "  $ cd docs"
      echo "  $ make websitedoc"
      echo "Then, commit and push changes of the website."
      ask 'continue'
      return
    fi

    # Check website sources are available.
    cd website
    if test ! $? -eq 0
    then
      echo "ERROR: cannot go to the website sources"
      ask 'continue'
      return
    fi
    # Stash any WIP in the website sources.
    git diff --quiet 2>/dev/null && git diff --quiet --cached 2>/dev/null || {
      echo "There is WIP in the website repository, stashing"
      echo "git stash create 'WIP during offlineimap API import'"
      git stash create 'WIP during offlineimap API import'
      ask 'continue'
    }

    cd .. # Back to offlineimap.git.
    update_website_releases_info
    cd "./$DOCSDIR" # Enter the docs directory in offlineimap.git.
    # Build the docs!
    make websitedoc && {
      # Commit changes in a branch.
      cd ../website # Enter the website sources.
      branch_name="import-$1"
      git checkout -b "$branch_name"
      git add '_doc/versions'
      git commit -a -s -m"update for offlineimap $1"
      echo "website: branch '$branch_name' ready for a merge in master!"
    }
    ask 'website updated locally; continue'
  fi
}


function git_username () {
  git config --get user.name
}
function git_usermail () {
  git config --get user.email
}

#
# $1: new version
#
function announce_header () {
  cat <<EOF
Message-Id: <$(git log HEAD~1.. --oneline --pretty='%H.%t.release.%ce')>
Date: $(git log HEAD~1.. --oneline --pretty='%cD')
From: $(git_username) <$(git_usermail)>
To: $MAILING_LIST
Subject: [ANNOUNCE] OfflineIMAP $1 released

OfflineIMAP $1 is out.

Downloads:
  http://github.com/OfflineIMAP/offlineimap/archive/${1}.tar.gz
  http://github.com/OfflineIMAP/offlineimap/archive/${1}.zip

Pip:
  pip install --user git+https://github.com/OfflineIMAP/offlineimap.git@${1}
EOF
}


function announce_footer () {
  cat <<EOF

-- 
$(git_username)
EOF
}


#
# $1: new version
# $2: previous version
#
function build_announce () {
  announce_header "$1" > "$TMP_ANNOUNCE"
  grep -v '^### OfflineIMAP' "$TMP_CHANGELOG_EXCERPT" | \
    grep -v '^#### Notes' >> "$TMP_ANNOUNCE"
  sed -i -r -e "s,^$ANNOUNCE_MAGIC,," "$TMP_ANNOUNCE"
  sed -i -r -e "s,^#### ,# ," "$TMP_ANNOUNCE"
  announce_footer >> "$TMP_ANNOUNCE"
}


function edit_announce () {
   edit_file 'edit announce' "$TMP_ANNOUNCE"
}



#
# run
#
function run () {
  debug 'in run'
  fix_pwd
  check_dirty
  prepare_env
  checkout_next
  clear
  welcome

  if test -f "$TMP_CHANGELOG_EXCERPT"
  then
    head "$TMP_CHANGELOG_EXCERPT"
    ask "A previous Changelog excerpt (head above) was found, use it?"
    if test ! $? -eq $Yes
    then
      mv -f "$TMP_CHANGELOG_EXCERPT" "$TMP_CHANGELOG_EXCERPT_OLD"
    fi
  fi

  previous_version="$(get_version)"
  message="Safety check: release after version:"
  ask "$message $previous_version ?"
  update_offlineimap_version
  new_version="$(get_version)"
  ask "Safety check: make a new release with version: '$new_version'" "Clear changes and restart"

  update_changelog "$new_version" "$previous_version"
  build_announce "$new_version" "$previous_version"
  edit_announce

  git_release $new_version

  update_website $new_version
}

run
cat <<EOF

Release is ready!
Make your checks and push the changes for both offlineimap and the website.
Announce template stands in '$TMP_ANNOUNCE'.
Command samples to do manually:
- git push <remote> master:master
- git push <remote> next:next
- git push <remote> $new_version
- python setup.py sdist && twine upload dist/* && rm -rf dist MANIFEST
- cd website
- git checkout master
- git merge $branch_name
- git push <remote> master:master
- cd ..
- git send-email $TMP_ANNOUNCE
Have fun! ,-)
EOF

# vim: expandtab ts=2 :
