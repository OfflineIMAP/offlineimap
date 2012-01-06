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

* Remove the old global locking system. We lock only the accounts that
  we currently sync, so you can invoke OfflineImap multiple times now as
  long as you sync different accounts. This system is compatible with
  all releases >= 6.4.0, so don't run older releases simultanous to this
  one.

Changes
-------

Bug Fixes
---------

* Fixed MachineUI to urlencode() output lines again, rather than
  outputting multi-line items. It's ugly as hell, but it had been that
  way for years.
