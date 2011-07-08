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

* Implement per-account locking, so that it will possible to sync
  different accounts at the same time. The old global lock is still in
  place for backward compatibility reasons (to be able to run old and
  new versions of OfflineImap concurrently) and will be removed in the
  future. Starting with this version, OfflineImap will be
  forward-compatible with the per-account locking style.

Changes
-------

* Documentation improvements concerning 'restoreatime' and some code cleanup

Bug Fixes
---------

* New emails are not created with "-rwxr-xr-x" but as "-rw-r--r--"
  anymore, fixing a regression in 6.3.4.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
