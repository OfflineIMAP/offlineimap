.. -*- coding: utf-8 -*-

.. _OfflineIMAP: https://github.com/nicolas33/offlineimap

===================
Hacking OfflineIMAP
===================

Welcome to the `OfflineIMAP`_ project. You'll find here all the information you
need to start hacking OfflineIMAP. Be aware there are a lot of very usefull tips
in the mailing list.  You may want to subscribe if you didn't, yet. This is
where you'll get help.

.. contents::
.. sectnum::


=================================
Git: Branching Model And Workflow
=================================

Introduction
============

In order to involve into OfflineIMAP you need some knowledges about Git and our
workflow. Don't be afraid if you don't know much, we would be pleased to help
you.

Release cycles
==============

We use a classical cycle based workflow:

1. A stable release is out.

2. Feature topics are sent, discussed and merged.

3. When enough work was merged, we start the freeze cycle: the first release
   candidate is out.

4. During the freeze cycle, no more features are merged. It's time to test
   OfflineIMAP. New candidates version are released. The more we are late in -rc
   releases the less patches are merged but bug fixes.

5. When we think a release is stable enough, we restart from step 1.


Branching model
===============

The branching model with use in OfflineIMAP is very near from the Git project.
We use a topic oriented workflow. A topic may be one or more patches.

The branches you'll find in the official repository are:

* gh-pages
* master
* next
* pu
* maint

gh-pages
--------

This comes from a feature offered by Github. We maintain the online home github
page using this branch.

master
------

If you're not sure what branch you should use, this one is for you.  This is the
mainline. Simple users should use this branch to follow OfflineIMAP's evolution.

Usually, patches submitted to the mailing list should start off of this branch.

next
----

Patches recently merged are good candidates for this branch. The content of next
is merged into the mainline (master) at release time for both stable and -rc
releases.

When patches are sent to the mailing list, contributors discuss about them. Once
done and when patches looks ready for mainline, patches are first merged into
next. Advanced users and testers use this branch to test last merged patches
before they hit the mainline. This helps not introducing strong breackages
directly in master.

pu
--

pu stands for "proposed updates". If a topic is not ready for master nor next,
it may be merged into pu. This branch only help developers to work on someone
else topic or an earlier pending topic.

This branch is **not intended to be checkouted**; never. Even developers don't
do that. Due to the way pu is built you can't expect content there to work in
any way... unless you clearly want to run into troubles.

Developers can extract a topic from this branch to work on it. See the following
section "Extract a topic from pu" in this documentation.

maint
-----

This is the maintenance branch. It gets its own releases starting from an old
stable release. It helps both users having troubles with last stable releases
and users not wanting latest features or so to still benefit from strong bug
fixes and security fixes.


Working with Git
================

Extract a topic from pu
-----------------------

pu is built this way::

  git checkout pu
  git reset --keep next
  git merge --no-ff -X theirs topic1
  git merge --no-ff -X theirs topic2
  git merge --no-ff -X theirs blue
  git merge --no-ff -X theirs orange
  ...

As a consequence:

1. Each topic merged uses a merge commit. A merge commit is a commit having 2
   ancestors. Actually, Git allows more than 2 parents but we don't use this
   feature. It's intended.

2. Paths in pu may mix up multiple versions if all the topics don't use the same
   base commit. This is very often the case as topics aren't rebased: it guarantees
   each topic is strictly identical to the last version sent to the mailing list.
   No surprise.


What you need to extract a particular topic is the sha1 of the tip of that
branch (the last commit of the topic). Assume you want the branch of the topic
called 'blue'. First, look at the log given by this command::

  git log --reverse --merges --parents origin/next..origin/pu

With this command you ask for the log:

* from next to pu
* in reverse order (older first)
* merge commits only
* with the sha1 of the ancestors

In this list, find the topic you're looking for, basing you search on the lines
like::

  Merge branch 'topic/name' into pu

By convention, it has the form <author_initials>/<brief_title>. When you're at
it, pick the topic ancestor sha1. It's always the last sha1 in the line starting
by 'commit'. For you to know:

* the first is the sha1 of the commit you see: the merge commit
* the following sha1 is the ancestor of the branch checkouted at merge time
  (always the previous merged topic or the ancien next in our case)
* last is the branch merged

Giving::

  commit sha1_of_merge_commit sha1_of_ancient_pu sha1_of_topic_blue

Then, you only have to checkout the topic from there::

  git checkout -b blue sha1_of_topic_blue

and you're done! You've just created a new branch called "blue" with the blue
content. Be aware this topic is almostly not updated against current next
branch. ,-)


===
API
===

API is documented in the dev-doc-src directory using the sphinx tools (also used
for python itself). This is a WIP. Contributions in this area would be very
appreciated.
