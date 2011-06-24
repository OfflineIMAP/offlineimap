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

* Added StartTLS support, it will automatically be used if the server
  supports it.

Changes
-------

Bug Fixes
---------


* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
* Implement IDLE feature. (delayed until next major release)
