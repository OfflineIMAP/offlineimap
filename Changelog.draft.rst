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

Bug Fixes
---------

* Syncing multiple accounts in single-threaded mode would fail as we try
  to "register" a thread as belonging to two accounts which was
  fatal. Make it non-fatal (it can be legitimate).

* New folders on the remote would be skipped on the very sync run they
  are created and only by synced in subsequent runs. Fixed.

* Make NOOPs to keep a server connection open more resistant against dropped 
  connections.
