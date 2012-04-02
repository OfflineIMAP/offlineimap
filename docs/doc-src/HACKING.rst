.. -*- coding: utf-8 -*-
.. _OfflineIMAP: http://offlineimap.org
.. _commits mailing list: http://lists.offlineimap.org/listinfo.cgi/commits-offlineimap.org
.. _mailing list: http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project

Hacking OfflineIMAP
===================

In this section you'll find all the information you need to start
hacking `OfflineIMAP`_. Be aware there are a lot of very usefull tips
in the mailing list.  You may want to subscribe if you didn't,
yet. This is where you will get help.

.. contents:: :depth: 2

API
---

:ref:`OfflineImap's API <API docs>` documentation is included in the user
documentation (next section) and online browsable at
`<http://docs.offlineimap.org>`_. It is mostly auto-generated from the
source code and is a work in progress. Contributions in this area
would be very appreciated.

Following new commits
---------------------

You can follow upstream commits on
  - `CIA.vc <http://cia.vc/stats/project/offlineimap>`,
  - `Ohloh <http://www.ohloh.net/p/offlineimap>`,
  - `GitHub <https://github.com/spaetz/offlineimap/commits/>`,
  - or on the `commits mailing list`_.



Git: OfflineImap's branching Model And Workflow
===============================================

Introduction
------------

This optional section provides you with information on how we use git
branches and do releases. You will need to know very little about git
to get started.

For the impatient, see the :ref:`contribution checklist` below.

Git Branching model
--------------------

OfflineIMAP uses the following branches:

 * master
 * next
 * maint
 * (pu)
 * & several topic oriented feature branches. A topic may consist of
   one or more patches.

master
++++++

If you're not sure what branch you should use, this one is for you.
This is the mainline. Simple users should use this branch to follow
OfflineIMAP's evolution.

Usually, patches submitted to the mailing list should start off of
this branch.

next
++++

Patches recently merged are good candidates for this branch. The content of next
is merged into the mainline (master) at release time for both stable and -rc
releases.

When patches are sent to the mailing list, contributors discuss about them. Once
done and when patches looks ready for mainline, patches are first merged into
next. Advanced users and testers use this branch to test last merged patches
before they hit the mainline. This helps not introducing strong breackages
directly in master.

pu
+++

pu stands for "proposed updates". If a topic is not ready for master nor next,
it may be merged into pu. This branch only help developers to work on someone
else topic or an earlier pending topic.

This branch is **not intended to be checkouted**; never. Even developers don't
do that. Due to the way pu is built you can't expect content there to work in
any way... unless you clearly want to run into troubles.

Developers can extract a topic from this branch to work on it. See the following
section "Extract a topic from pu" in this documentation.

maint
+++++

This is the maintenance branch. It gets its own releases starting from an old
stable release. It helps both users having troubles with last stable releases
and users not wanting latest features or so to still benefit from strong bug
fixes and security fixes.

Release cycles
--------------

A typical release cycle works like this:

1. A stable release is out.

2. Feature topics are sent, discussed and merged.

3. When enough work was merged, we start the freeze cycle: the first release
   candidate is out.

4. During the freeze cycle, no more features are merged. It's time to test
   OfflineIMAP. New candidates version are released. The more we are late in -rc
   releases the less patches are merged but bug fixes.

5. When we think a release is stable enough, we restart from step 1.


.. _contribution checklist:


Contribution Checklist (and a short version for the impatient)
===============================================================

Create commits
--------------

* make commits of logical units
* check for unnecessary whitespace with ``git diff --check``
  before committing
* do not check in commented out code or unneeded files
* the first line of the commit message should be a short
  description (50 characters is the soft limit, see DISCUSSION
  in git-commit(1)), and should skip the full stop
* the body should provide a meaningful commit message, which:
	* uses the imperative, present tense: **change**,
	  not **changed** or **changes**.
	* includes motivation for the change, and contrasts
	  its implementation with previous behaviour
* add a ``Signed-off-by: Your Name <you@example.com>`` line to the
  commit message (or just use the option `-s` when committing)
  to confirm that you agree to the **Developer's Certificate of Origin**
* make sure that you have tests for the bug you are fixing
* make sure that the test suite passes after your commit


Export commits as patches
-------------------------

* use ``git format-patch -M`` to create the patch
* do not PGP sign your patch
* do not attach your patch, but read in the mail
  body, unless you cannot teach your mailer to
  leave the formatting of the patch alone.
* be careful doing cut & paste into your mailer, not to
  corrupt whitespaces.
* provide additional information (which is unsuitable for
  the commit message) between the ``---`` and the diffstat
* if you change, add, or remove a command line option or
  make some other user interface change, the associated
  documentation should be updated as well.
* if your name is not writable in ASCII, make sure that
  you send off a message in the correct encoding.
* send the patch to the `mailing list`_ and the
  maintainer (nicolas.s-dev@laposte.net) if (and only if)
  the patch is ready for inclusion. If you use `git-send-email(1)`,
  please test it first by sending email to yourself.
* see below for instructions specific to your mailer



Long version
------------

I started reading over the SubmittingPatches document for Git, primarily because
I wanted to have a document similar to it for OfflineIMAP to make sure people
understand what they are doing when they write `Signed-off-by` line.

But the patch submission requirements are a lot more relaxed here on the
technical/contents front, because the OfflineIMAP is a lot smaller ;-).  So here
is only the relevant bits.

Decide what branch to base your work on
+++++++++++++++++++++++++++++++++++++++

In general, always base your work on the oldest branch that your
change is relevant to.

* A bugfix should be based on 'maint' in general. If the bug is not
  present in 'maint', base it on 'master'. For a bug that's not yet
  in 'master', find the topic that introduces the regression, and
  base your work on the tip of the topic.
* A new feature should be based on 'master' in general. If the new
  feature depends on a topic that is in 'pu', but not in 'master',
  base your work on the tip of that topic.
* Corrections and enhancements to a topic not yet in 'master' should
  be based on the tip of that topic. If the topic has not been merged
  to 'next', it's alright to add a note to squash minor corrections
  into the series.
* In the exceptional case that a new feature depends on several topics
  not in 'master', start working on 'next' or 'pu' privately and send
  out patches for discussion. Before the final merge, you may have to
  wait until some of the dependent topics graduate to 'master', and
  rebase your work.

To find the tip of a topic branch, run ``git log --first-parent
master..pu`` and look for the merge commit. The second parent of this
commit is the tip of the topic branch.

Make separate commits for logically separate changes
++++++++++++++++++++++++++++++++++++++++++++++++++++

Unless your patch is really trivial, you should not be sending your
changes in a single patch.  Instead, always make a commit with
complete commit message and generate a series of small patches from
your repository.

Describe the technical detail of the change(s).

If your description starts to get too long, that's a sign that you
probably need to split up your commit to finer grained pieces.
That being said, patches which plainly describe the things that
help reviewers check the patch, and future maintainers understand
the code, are the most beautiful patches.  Descriptions that summarise
the point in the subject well, and describe the motivation for the
change, the approach taken by the change, and if relevant how this
differs substantially from the prior version, can be found on Usenet
archives back into the late 80's.  Consider it like good Netiquette,
but for code.


Generate your patch using git tools out of your commits
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

git based diff tools (git, Cogito, and StGIT included) generate
unidiff which is the preferred format.

You do not have to be afraid to use -M option to ``git diff`` or
``git format-patch``, if your patch involves file renames.  The
receiving end can handle them just fine.

Please make sure your patch does not include any extra files
which do not belong in a patch submission.  Make sure to review
your patch after generating it, to ensure accuracy.  Before
sending out, please make sure it cleanly applies to the "master"
branch head.  If you are preparing a work based on "next" branch,
that is fine, but please mark it as such.


Sending your patches
++++++++++++++++++++

People on the mailing list need to be able to read and
comment on the changes you are submitting.  It is important for
a developer to be able to "quote" your changes, using standard
e-mail tools, so that they may comment on specific portions of
your code.  For this reason, all patches should be submitted
"inline".  WARNING: Be wary of your MUAs word-wrap
corrupting your patch.  Do not cut-n-paste your patch; you can
lose tabs that way if you are not careful.

It is a common convention to prefix your subject line with
[PATCH].  This lets people easily distinguish patches from other
e-mail discussions.  Use of additional markers after PATCH and
the closing bracket to mark the nature of the patch is also
encouraged.  E.g. [PATCH/RFC] is often used when the patch is
not ready to be applied but it is for discussion, [PATCH v2],
[PATCH v3] etc. are often seen when you are sending an update to
what you have previously sent.

``git format-patch`` command follows the best current practice to
format the body of an e-mail message.  At the beginning of the
patch should come your commit message, ending with the
Signed-off-by: lines, and a line that consists of three dashes,
followed by the diffstat information and the patch itself.  If
you are forwarding a patch from somebody else, optionally, at
the beginning of the e-mail message just before the commit
message starts, you can put a "From: " line to name that person.

You often want to add additional explanation about the patch,
other than the commit message itself.  Place such "cover letter"
material between the three dash lines and the diffstat.

Do not attach the patch as a MIME attachment, compressed or not.
Do not let your e-mail client send quoted-printable.  Do not let
your e-mail client send format=flowed which would destroy
whitespaces in your patches. Many
popular e-mail applications will not always transmit a MIME
attachment as plain text, making it impossible to comment on
your code.  A MIME attachment also takes a bit more time to
process.  This does not decrease the likelihood of your
MIME-attached change being accepted, but it makes it more likely
that it will be postponed.

Exception:  If your mailer is mangling patches then someone may ask
you to re-send them using MIME, that is OK.

Do not PGP sign your patch, at least for now.  Most likely, your
maintainer or other people on the list would not have your PGP
key and would not bother obtaining it anyway.  Your patch is not
judged by who you are; a good patch from an unknown origin has a
far better chance of being accepted than a patch from a known,
respected origin that is done poorly or does incorrect things.

If you really really really really want to do a PGP signed
patch, format it as "multipart/signed", not a text/plain message
that starts with '-----BEGIN PGP SIGNED MESSAGE-----'.  That is
not a text/plain, it's something else.

Unless your patch is a very trivial and an obviously correct one,
first send it with "To:" set to the mailing list, with "cc:" listing
people who are involved in the area you are touching (the output from
"git blame $path" and "git shortlog --no-merges $path" would help to
identify them), to solicit comments and reviews.  After the list
reached a consensus that it is a good idea to apply the patch, re-send
it with "To:" set to the maintainer and optionally "cc:" the list for
inclusion.  Do not forget to add trailers such as "Acked-by:",
"Reviewed-by:" and "Tested-by:" after your "Signed-off-by:" line as
necessary.


Sign your work
++++++++++++++

To improve tracking of who did what, we've borrowed the
"sign-off" procedure from the Linux kernel project on patches
that are being emailed around.  Although OfflineIMAP is a lot
smaller project it is a good discipline to follow it.

The sign-off is a simple line at the end of the explanation for
the patch, which **certifies that you wrote it or otherwise have
the right to pass it on as a open-source patch**.  The rules are
pretty simple: if you can certify the below:

**Developer's Certificate of Origin 1.1**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  By making a contribution to this project, I certify that:

  (a) The contribution was created in whole or in part by me and I
      have the right to submit it under the open source license
      indicated in the file; or

  (b) The contribution is based upon previous work that, to the best
      of my knowledge, is covered under an appropriate open source
      license and I have the right under that license to submit that
      work with modifications, whether created in whole or in part
      by me, under the same open source license (unless I am
      permitted to submit under a different license), as indicated
      in the file; or

  (c) The contribution was provided directly to me by some other
          person who certified (a), (b) or (c) and I have not modified
          it.

  (d) I understand and agree that this project and the contribution
	    are public and that a record of the contribution (including all
	    personal information I submit with it, including my sign-off) is
	    maintained indefinitely and may be redistributed consistent with
	    this project or the open source license(s) involved.

then you just add a line saying

	Signed-off-by: Random J Developer <random@developer.example.org>

This line can be automatically added by git if you run the git-commit
command with the -s option.

Notice that you can place your own Signed-off-by: line when
forwarding somebody else's patch with the above rules for
D-C-O.  Indeed you are encouraged to do so.  Do not forget to
place an in-body "From: " line at the beginning to properly attribute
the change to its true author (see above).

Also notice that a real name is used in the Signed-off-by: line. Please
don't hide your real name.

If you like, you can put extra tags at the end:

* "Reported-by:" is used to to credit someone who found the bug that
   the patch attempts to fix.
* "Acked-by:" says that the person who is more familiar with the area
   the patch attempts to modify liked the patch.
* "Reviewed-by:", unlike the other tags, can only be offered by the
   reviewer and means that she is completely satisfied that the patch
   is ready for application.  It is usually offered only after a
   detailed review.
* "Tested-by:" is used to indicate that the person applied the patch
   and found it to have the desired effect.

You can also create your own tag or use one that's in common usage
such as "Thanks-to:", "Based-on-patch-by:", or "Mentored-by:".

An ideal patch flow
===================

Here is an ideal patch flow for this project the current maintainer
suggests to the contributors:

 (0) You come up with an itch.  You code it up.

 (1) Send it to the list and cc people who may need to know about
     the change.

     The people who may need to know are the ones whose code you
     are butchering.  These people happen to be the ones who are
     most likely to be knowledgeable enough to help you, but
     they have no obligation to help you (i.e. you ask for help,
     don't demand).  ``git log -p -- $area_you_are_modifying`` would
     help you find out who they are.

 (2) You get comments and suggestions for improvements.  You may
     even get them in a "on top of your change" patch form.

 (3) Polish, refine, and re-send to the list and the people who
     spend their time to improve your patch.  Go back to step (2).

 (4) The list forms consensus that the last round of your patch is
     good.  Send it to the list and cc the maintainer.

 (5) A topic branch is created with the patch and is merged to 'next',
     and cooked further and eventually graduates to 'master'.

In any time between the (2)-(3) cycle, the maintainer may pick it up
from the list and queue it to 'pu', in order to make it easier for
people play with it without having to pick up and apply the patch to
their trees themselves.

Know the status of your patch after submission
----------------------------------------------

* You can use Git itself to find out when your patch is merged in
  master. ``git pull --rebase`` will automatically skip already-applied
  patches, and will let you know. This works only if you rebase on top
  of the branch in which your patch has been merged (i.e. it will not
  tell you if your patch is merged in pu if you rebase on top of
  master).
 
.. * Read the git mailing list, the maintainer regularly posts messages
  entitled "What's cooking in git.git" and "What's in git.git" giving
  the status of various proposed changes.

MUA specific hints
==================

Some of patches I receive or pick up from the list share common
patterns of breakage.  Please make sure your MUA is set up
properly not to corrupt whitespaces.  Here are two common ones
I have seen:

* Empty context lines that do not have _any_ whitespace.

* Non empty context lines that have one extra whitespace at the
  beginning.

One test you could do yourself if your MUA is set up correctly is:

* Send the patch to yourself, exactly the way you would, except
  To: and Cc: lines, which would not contain the list and
  maintainer address.

* Save that patch to a file in UNIX mailbox format.  Call it say
  a.patch.

* Try to apply to the tip of the "master" branch from the
  git.git public repository::

    $ git fetch http://kernel.org/pub/scm/git/git.git master:test-apply
    $ git checkout test-apply
    $ git reset --hard
    $ git am a.patch

If it does not apply correctly, there can be various reasons.

* Your patch itself does not apply cleanly.  That is _bad_ but
  does not have much to do with your MUA.  Please rebase the
  patch appropriately.

* Your MUA corrupted your patch; "am" would complain that
  the patch does not apply.  Look at .git/rebase-apply/ subdirectory and
  see what 'patch' file contains and check for the common
  corruption patterns mentioned above.

* While you are at it, check what are in 'info' and
  'final-commit' files as well.  If what is in 'final-commit' is
  not exactly what you would want to see in the commit log
  message, it is very likely that your maintainer would end up
  hand editing the log message when he applies your patch.
  Things like "Hi, this is my first patch.\n", if you really
  want to put in the patch e-mail, should come after the
  three-dash line that signals the end of the commit message.


Pine
----

(Johannes Schindelin)
  I don't know how many people still use pine, but for those poor souls it may
  be good to mention that the quell-flowed-text is needed for recent versions.

  ... the "no-strip-whitespace-before-send" option, too. AFAIK it was introduced
  in 4.60.

(Linus Torvalds)
  And 4.58 needs at least this

::

  ---
  diff-tree 8326dd8350be64ac7fc805f6563a1d61ad10d32c (from e886a61f76edf5410573e92e38ce22974f9c40f1)
  Author: Linus Torvalds <torvalds@g5.osdl.org>
  Date:   Mon Aug 15 17:23:51 2005 -0700

      Fix pine whitespace-corruption bug

      There's no excuse for unconditionally removing whitespace from
      the pico buffers on close.

  diff --git a/pico/pico.c b/pico/pico.c
  --- a/pico/pico.c
  +++ b/pico/pico.c
  @@ -219,7 +219,9 @@ PICO *pm;
  	    switch(pico_all_done){	/* prepare for/handle final events */
  	      case COMP_EXIT :		/* already confirmed */
  		packheader();
  +#if 0
  		stripwhitespace();
  +#endif
  		c |= COMP_EXIT;
  		break;

(Daniel Barkalow)
  > A patch to SubmittingPatches, MUA specific help section for
  > users of Pine 4.63 would be very much appreciated.

  Ah, it looks like a recent version changed the default behavior to do the
  right thing, and inverted the sense of the configuration option. (Either
  that or Gentoo did it.) So you need to set the
  "no-strip-whitespace-before-send" option, unless the option you have is
  "strip-whitespace-before-send", in which case you should avoid checking
  it.


Thunderbird
-----------

(A Large Angry SCM)
  By default, Thunderbird will both wrap emails as well as flag them as
  being 'format=flowed', both of which will make the resulting email unusable
  by git.

  Here are some hints on how to successfully submit patches inline using
  Thunderbird.

  There are two different approaches.  One approach is to configure
  Thunderbird to not mangle patches.  The second approach is to use
  an external editor to keep Thunderbird from mangling the patches.

**Approach #1 (configuration):**

  This recipe is current as of Thunderbird 2.0.0.19.  Three steps:

    1. Configure your mail server composition as plain text
       Edit...Account Settings...Composition & Addressing,
       uncheck 'Compose Messages in HTML'.
    2. Configure your general composition window to not wrap
       Edit..Preferences..Composition, wrap plain text messages at 0
    3. Disable the use of format=flowed
       Edit..Preferences..Advanced..Config Editor.  Search for:
       mailnews.send_plaintext_flowed
       toggle it to make sure it is set to 'false'.

  After that is done, you should be able to compose email as you
  otherwise would (cut + paste, git-format-patch | git-imap-send, etc),
  and the patches should not be mangled.

**Approach #2 (external editor):**

This recipe appears to work with the current [*1*] Thunderbird from Suse.

The following Thunderbird extensions are needed:
  AboutConfig 0.5
	  http://aboutconfig.mozdev.org/
  External Editor 0.7.2
	  http://globs.org/articles.php?lng=en&pg=8


1) Prepare the patch as a text file using your method of choice.

2) Before opening a compose window, use Edit->Account Settings to
   uncheck the "Compose messages in HTML format" setting in the
   "Composition & Addressing" panel of the account to be used to send the
   patch. [*2*]

3) In the main Thunderbird window, _before_ you open the compose window
   for the patch, use Tools->about:config to set the following to the
   indicated values::

     mailnews.send_plaintext_flowed	=> false
     mailnews.wraplength		=> 0

4) Open a compose window and click the external editor icon.

5) In the external editor window, read in the patch file and exit the
   editor normally.

6) Back in the compose window: Add whatever other text you wish to the
   message, complete the addressing and subject fields, and press send.

7) Optionally, undo the about:config/account settings changes made in
   steps 2 & 3.


[Footnotes]

*1* Version 1.0 (20041207) from the MozillaThunderbird-1.0-5 rpm of Suse
9.3 professional updates.

*2* It may be possible to do this with about:config and the following
settings but I haven't tried, yet::

  mail.html_compose			=> false
  mail.identity.default.compose_html	=> false
  mail.identity.id?.compose_html		=> false

(Lukas Sandström)
  There is a script in contrib/thunderbird-patch-inline which can help you
  include patches with Thunderbird in an easy way. To use it, do the steps above
  and then use the script as the external editor.

Gnus
----

'|' in the *Summary* buffer can be used to pipe the current
message to an external program, and this is a handy way to drive
"git am".  However, if the message is MIME encoded, what is
piped into the program is the representation you see in your
*Article* buffer after unwrapping MIME.  This is often not what
you would want for two reasons.  It tends to screw up non ASCII
characters (most notably in people's names), and also
whitespaces (fatal in patches).  Running 'C-u g' to display the
message in raw form before using '|' to run the pipe can work
this problem around.


KMail
-----

This should help you to submit patches inline using KMail.

1) Prepare the patch as a text file.

2) Click on New Mail.

3) Go under "Options" in the Composer window and be sure that
   "Word wrap" is not set.

4) Use Message -> Insert file... and insert the patch.

5) Back in the compose window: add whatever other text you wish to the
   message, complete the addressing and subject fields, and press send.


Gmail
-----

GMail does not appear to have any way to turn off line wrapping in the web
interface, so this will mangle any emails that you send.  You can however
use "git send-email" and send your patches through the GMail SMTP server, or
use any IMAP email client to connect to the google IMAP server and forward
the emails through that.

To use ``git send-email`` and send your patches through the GMail SMTP server,
edit `~/.gitconfig` to specify your account settings::

  [sendemail]
	  smtpencryption = tls
	  smtpserver = smtp.gmail.com
	  smtpuser = user@gmail.com
	  smtppass = p4ssw0rd
	  smtpserverport = 587

Once your commits are ready to be sent to the mailing list, run the
following commands::

  $ git format-patch --cover-letter -M origin/master -o outgoing/
  $ edit outgoing/0000-*
  $ git send-email outgoing/*

To submit using the IMAP interface, first, edit your `~/.gitconfig` to specify your
account settings::

  [imap]
	  folder = "[Gmail]/Drafts"
	  host = imaps://imap.gmail.com
	  user = user@gmail.com
	  pass = p4ssw0rd
	  port = 993
	  sslverify = false

You might need to instead use: folder = "[Google Mail]/Drafts" if you get an error
that the "Folder doesn't exist".

Once your commits are ready to be sent to the mailing list, run the
following commands::

  $ git format-patch --cover-letter -M --stdout origin/master | git imap-send

Just make sure to disable line wrapping in the email client (GMail web
interface will line wrap no matter what, so you need to use a real
IMAP client).

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
