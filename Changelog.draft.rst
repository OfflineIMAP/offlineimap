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

Bug Fixes
---------
