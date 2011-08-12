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

* When a message upload/download fails, we do not abort the whole folder
  synchronization, but only skip that message, informing the user at the
  end of the sync run.
 
Changes
-------

* Refactor our IMAPServer class. Background work without user-visible
  changes.

Bug Fixes
---------

* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
