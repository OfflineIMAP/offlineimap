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
* Implement UIDPLUS extension support. OfflineIMAP will now not insert
  an X-OfflineIMAP header if the mail server supports the UIDPLUS
  extension.
* SSL: support subjectAltName.

Changes
-------

* Makefile use magic to find the version number.
* Rework the repository module
* Change UI names to Blinkenlights,TTYUI,Basic,Quiet,MachineUI.
  Old names will still work, but are deprecated.
  Document that we don't accept a list of UIs anymore.
* Reworked the syncing strategy. The only user-visible change is that  
  blowing away LocalStatus will not require you to redownload ALL of
  your mails if you still have the local Maildir. It will simply
  recreate LocalStatus.

Bug Fixes
---------

* Allow SSL connections to send keep-alive messages.
* Fix regression (UIBase is no more).
* Make profiling mode really enforce single-threading
* Do not send localized date strings to the IMAP server as it will
  either ignore or refuse them.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)


Stalled
=======

* Learn Sqlite support.
    Stalled: it would need to learn the ability to choose between the current
    format and SQL to help testing the long term.
