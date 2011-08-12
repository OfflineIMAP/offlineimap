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

Bug Fixes
---------

* Selecting inexistent folders specified in folderincludes now throws
  nice errors and continues to sync with all other folders rather than
  exiting offlineimap with a traceback.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
