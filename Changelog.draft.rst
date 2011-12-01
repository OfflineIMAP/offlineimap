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

* add a --info command line switch that outputs useful information about
  the server and the configuration for all enabled accounts.

Changes
-------

* Reworked logging which was reported to e.g. not flush output to files
  often enough. User-visible changes:
  a) console output goes to stderr (for now).
  b) file output has timestamps and looks identical in the basic and
  ttyui UIs.
  c) File output should be flushed after logging by default (do
  report if not).

* Bumped bundled imaplib2 to release 2.29

Bug Fixes
---------

* IMAP<->IMAP sync with a readonly local IMAP repository failed with a
  rather mysterious "TypeError: expected a character buffer object"
  error. Fix this my retrieving the list of folders early enough even
  for readonly repositories.

* Fix regression from 6.4.0. When using local Maildirs with "/" as a
  folder separator, all folder names would get a trailing slash
  appended, which is plain wrong.
