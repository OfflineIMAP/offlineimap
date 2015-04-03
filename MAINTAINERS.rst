.. -*- coding: utf-8 -*-

Official maintainers
====================

Eygene Ryabinkin
  email: rea at freebsd.org
  github: konvpalto

Sebastian Spaeth
  email: sebastian at sspaeth.de
  github: spaetz

Nicolas Sebrecht
  email: nicolas.s-dev at laposte.net
  github: nicolas33

Mailing List maintainers
========================

Eygene Ryabinkin
  email: rea at freebsd.org

Sebastian Spaeth
  email: sebastian at sspaeth.de

Nicolas Sebrecht
  email: nicolas.s-dev at laposte.net


How to maintain the source code
===============================

Rolling out a new release
-------------------------

1. Update the Changelogs.
2. Update the version in ``offlineimap/__init__.py``.
3. Commit the changes with the version in the commit message.
4. Tag the release.
5. Wait the next day before pushing out the release.
6. Make an announce to the mailing list.


Tagging stable releases or release candidates
'''''''''''''''''''''''''''''''''''''''''''''

It is done via Git's ``tag`` command, but you **must** do ``git tag -a``
to create annotated tag.

Release tags are named ``vX.Y.Z`` and release candidate tags are named
``vX.Y.Z-rcN``.


How to become a core team maintainer
====================================

Express your desire to one of the current official maintainers. This is all you
have to do.

We don't require years of contributions. Of course, we will pay attention a bit
to your past interest to the project and your skills. But nothing is mandatory
and it's fine to still be learning while being an official maintainer. Nobody is
all-knowing, even with years of experience. So, if one current maintainer
agrees, he will grant you the write access to the official repository.

Contrary to what most people might think, becoming an official maintainer is not
something hard. You'll first be asked to merge contributions and make one or two
official releases. We will review your first steps and nothing more.

Be aware that there is no more leader maintainer, neither is a leader in the
team. Once you become a team member and did some maintenance for the project,
you're free to take all the strong decisions.

Since we are a team, we always try to discuss with others before taking any
strong decision, including the users. This prevents from breaking things inside
the whole community and the proximity we have with our users. Even most discreet
of them will raise one day with good hints, review, feedback or opinion. This is
how we are running in OfflineIMAP. And yes, we are really proud about the solid
relationship we have with the users.

Also, we are all benevolent volunteers. We are in a very good position to know
that we are not always free to contribute as much as we'd like to. Being away
for some (long) time is not a problem. At the time of this writing, each
maintainer took some vacations from the project at some point in time. You'll
contribute as much as your free time permits. It's fine! We are a team, so we
help each other.

Welcome! ,-)
