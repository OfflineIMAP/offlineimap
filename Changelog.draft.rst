=========
ChangeLog
=========

Users should ignore this content: **it is draft**.

Contributors should add entries here in the following section, on top of the
others.

`WIP (coming releases)`
=======================

New Features
------------

* --dry-run mode protects us from performing any actual action.
    It will not precisely give the exact information what will
    happen. If e.g. it would need to create a folder, it merely
    outputs "Would create folder X", but not how many and which mails
    it would transfer.

Changes
-------

* internal code changes to prepare for Python3

* Improve user documentation of nametrans/folderfilter

* Fixed some cases where invalid nametrans rules were not caught and
  we would not propagate local folders to the remote repository.
  (now tested in test03)

* Revert "* Slight performance enhancement uploading mails to an IMAP
  server in the common case." It might have led to instabilities.

* Revamped documentation structure. `make` in the `docs` dir or `make
  doc` in the root dir will now create the 1) man page and 2) the user
  documentation using sphinx (requiring python-doctools, and
  sphinx). The resulting user docs are in `docs/html`. You can also
  only create the man pages with `make man` in the `docs` dir.

* -f command line option only works on the untranslated remote
  repository folder names now. Previously folderfilters had to match
  both the local AND remote name which caused unwanted behavior in
  combination with nametrans rules. Clarify in the help text.

* Some better output when using nonsensical configuration settings

Bug Fixes
---------
