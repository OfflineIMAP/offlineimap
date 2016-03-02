[offlineimap]: http://github.com/OfflineIMAP/offlineimap
[website]: http://www.offlineimap.org
[wiki]: http://github.com/OfflineIMAP/offlineimap/wiki
[blog]: http://www.offlineimap.org/posts.html

# OfflineIMAP

***Get the emails where you need them.***

## Description

OfflineIMAP is a software to dispose your e-mail mailbox(es) as a **local
Maildir**. OfflineIMAP will synchronize both sides via *IMAP*.

The main downside about IMAP is that you have to **trust** your email provider to
not lose your mails. This is not something impossible while not very common.
With OfflineIMAP, you can download your Mailboxes and make you own backups of
the [Maildir](https://en.wikipedia.org/wiki/Maildir).

This allows reading your email while offline without the need for the mail
reader (MUA) to support IMAP disconnected operations. Need an attachment from a
message without internet connection? It's fine, the message is still there.


## Project status and future

> As one of the maintainer of OfflineIMAP, I'd like to put my efforts into
> [imapfw](http://github.com/OfflineIMAP/imapfw). **imapfw** is a software in
> development that I intend to replace OfflineIMAP in the long term.
>
> That's why I'm not going to do development in OfflineIMAP. I continue to do
> the maintenance job in OfflineIMAP: fixing small bugs, (quick)
> reviewing/merging patches and rolling out new releases, but that's all.
>
> While I keep tracking issues for OfflineIMAP, you should not expect support
> much from me anymore.
>
> You won't be left at the side. OfflineIMAP's community is large enough so that
> you'll find people for most of your issues.
>
> Get news from the [blog][blog].
>
>                                  Nicolas Sebrecht. ,-)


## License

GNU General Public License v2.


## Why should I use OfflineIMAP?

* It is **fast**.
* It is **reliable**.
* It is **flexible**.
* It is **safe**.

## Downloads

You should first check if your distribution already packages OfflineIMAP for you.
Downloads releases as [tarball or zipball](https://github.com/OfflineIMAP/offlineimap/tags).


## Feedbacks and contributions

**The user discussions, development, announcements and all the exciting stuff take
place on the mailing list.** While not mandatory to send emails, you can
[subscribe here](http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project).

Bugs, issues and contributions can be requested to both the mailing list or the
[official Github project][offlineimap].


## The community

* OfflineIMAP's main site is the [project page at Github][offlineimap].
* There is the [OfflineIMAP community's website][website].
* And finally, [the wiki][wiki].


## Requirements

* Python v2.7
* Python SQlite (optional while recommended)
* Python json and urllib (used for XOAuth2 authentication)


## Documentation

All the current and updated documentation is at the [community's website][website].

### Read documentation locally

You might want to read the documentation locally. Get the sources of the website.
For the other documentation, run the appropriate make target:
```
$ ./scripts/get-repository.sh website
$ cd docs
$ make html  # Requires rst2html
$ make man   # Requires a2x
$ make api   # Requires sphinx
```
