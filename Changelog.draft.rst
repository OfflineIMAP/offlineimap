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
 
* If you connect via ssl and 'cert_fingerprint' is configured, we check
  that the server certificate is actually known and identical by
  comparing the stored sha1 fingerprint with the current one.

Changes
-------

* Refactor our IMAPServer class. Background work without user-visible
  changes.
* Remove the configurability of the Blinkenlights statuschar. It
  cluttered the main configuration file for little gain.
* Updated bundled imaplib2 to version 2.28.

Bug Fixes
---------

* We protect more robustly against asking for inexistent messages from the
  IMAP server, when someone else deletes or moves messages while we sync.
* Selecting inexistent folders specified in folderincludes now throws
  nice errors and continues to sync with all other folders rather than
  exiting offlineimap with a traceback.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
