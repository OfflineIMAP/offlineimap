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

* Make ctrl-c exit cleanly rather aborting brutally (which could leave
  around temporary files, half-written cache files, etc). Exiting on
  SIGTERM and CTRL-C can take a little longer, but will be clean.

Bug Fixes
---------
