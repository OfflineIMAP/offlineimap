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

* Make folders containing quotes work rather than crashing
  (reported by Mark Eichin)

Changes
-------

* Slight performance enhancement uploading mails to an IMAP server in the
  common case.

Bug Fixes
---------

* Fix python2.6 compatibility with the TTYUI backend (crash)
* Fix TTYUI regression from 6.5.2 in refresh loop (crash)
* Fix crashes related to UIDVALIDITY returning "None"
