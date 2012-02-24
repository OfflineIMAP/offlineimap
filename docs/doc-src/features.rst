Description
===========

OfflineIMAP is a tool to simplify your e-mail reading. With OfflineIMAP, you can
read the same mailbox from multiple computers. You get a current copy of your
messages on each computer, and changes you make one place will be visible on all
other systems. For instance, you can delete a message on your home computer, and
it will appear deleted on your work computer as well. OfflineIMAP is also useful
if you want to use a mail reader that does not have IMAP support, has poor IMAP
support, or does not provide disconnected operation.

OfflineIMAP works on pretty much any POSIX operating system, such as Linux, BSD
operating systems, MacOS X, Solaris, etc.

OfflineIMAP is a Free Software project licensed under the GNU General Public
License. You can download it for free, and you can modify it. In fact, you are
encouraged to contribute to OfflineIMAP, and doing so is fast and easy.

OfflineIMAP is FAST; it synchronizes my two accounts with over 50 folders in 3
seconds.  Other similar tools might take over a minute, and achieve a
less-reliable result.  Some mail readers can take over 10 minutes to do the same
thing, and some don't even support it at all.  Unlike other mail tools,
OfflineIMAP features a multi-threaded synchronization algorithm that can
dramatically speed up performance in many situations by synchronizing several
different things simultaneously.

OfflineIMAP is FLEXIBLE; you can customize which folders are synced via regular
expressions, lists, or Python expressions; a versatile and comprehensive
configuration file is used to control behavior; two user interfaces are
built-in; fine-tuning of synchronization performance is possible; internal or
external automation is supported; SSL and PREAUTH tunnels are both supported;
offline (or "unplugged") reading is supported; and esoteric IMAP features are
supported to ensure compatibility with the widest variety of IMAP servers.

OfflineIMAP is SAFE; it uses an algorithm designed to prevent mail loss at all
costs.  Because of the design of this algorithm, even programming errors should
not result in loss of mail.  I am so confident in the algorithm that I use my
own personal and work accounts for testing of OfflineIMAP pre-release,
development, and beta releases.  Of course, legally speaking, OfflineIMAP comes
with no warranty, so I am not responsible if this turns out to be wrong.

.. note: OfflineImap was written by John Goerzen, who retired from
    maintaining.  It is now maintained by Nicolas Sebrecht & Sebastian
    Spaeth at https://github.com/spaetz/offlineimap. Thanks to John
    for his great job and to have share this project with us.

Method of Operation
===================

OfflineIMAP traditionally operates by maintaining a hierarchy of mail folders in
Maildir format locally.  Your own mail reader will read mail from this tree, and
need never know that the mail comes from IMAP.  OfflineIMAP will detect changes
to the mail folders on your IMAP server and your own computer and
bi-directionally synchronize them, copying, marking, and deleting messages as
necessary.

With OfflineIMAP 4.0, a powerful new ability has been introduced ― the program
can now synchronize two IMAP servers with each other, with no need to have a
Maildir layer in-between.  Many people use this if they use a mail reader on
their local machine that does not support Maildirs.  People may install an IMAP
server on their local machine, and point both OfflineIMAP and their mail reader
of choice at it.  This is often preferable to the mail reader's own IMAP support
since OfflineIMAP supports many features (offline reading, for one) that most
IMAP-aware readers don't.  However, this feature is not as time-tested as
traditional syncing, so my advice is to stick with normal methods of operation
for the time being.
