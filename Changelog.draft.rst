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

Changes
-------

* Do not attempt to sync lower case custom Maildir flags. We do not
  support them (yet)
* Add filter information to the filter list in --info output

Bug Fixes
---------

* Fix possible crash during --info run
* Fix reading in Maildirs, where we would attempt to create empty
  directories on REMOTE.
