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

Bug Fixes
---------

* IMAP<->IMAP sync with a readonly local IMAP repository failed with a
  rather mysterious "TypeError: expected a character buffer object"
  error. Fix this my retrieving the list of folders early enough even
  for readonly repositories.
