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

* Indicate progress when copying many messages (slightly change log format)

* Output how long an account sync took (min:sec).

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

* Syncing multiple accounts in single-threaded mode would fail as we try
  to "register" a thread as belonging to two accounts which was
  fatal. Make it non-fatal (it can be legitimate).

* New folders on the remote would be skipped on the very sync run they
  are created and only by synced in subsequent runs. Fixed.

* Make NOOPs to keep a server connection open more resistant against dropped 
  connections.

* a readonly parameter to select() was not always treated correctly,
  which could result in some folders being opened read-only when we
  really needed read-write.
