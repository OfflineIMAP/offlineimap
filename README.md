[offlineimap]: http://github.com/OfflineIMAP/offlineimap
[website]: http://www.offlineimap.org
[wiki]: http://github.com/OfflineIMAP/offlineimap/wiki
[blog]: http://www.offlineimap.org/posts.html

# OfflineIMAP

***"Get the emails where you need them."***

[Official offlineimap][offlineimap].


## Description

OfflineIMAP is software that downloads your email mailbox(es) as **local
Maildirs**. OfflineIMAP will synchronize both sides via *IMAP*.

IMAP's main downside is that you have to **trust** your email provider to
not lose your email. While certainly unlikely, it's not impossible.
With OfflineIMAP, you can download your Mailboxes and make you own backups of
your [Maildir](https://en.wikipedia.org/wiki/Maildir).

This allows reading your email offline without the need for your mail
reader (MUA) to support IMAP operations. Need an attachment from a
message without internet connection? No problem, the message is still there.


## Project status and future

> As one of the maintainer of OfflineIMAP, I'd like to put my efforts into
> [imapfw](http://github.com/OfflineIMAP/imapfw). **imapfw** is software in
> development that I intend to replace OfflineIMAP with in the long term.
>
> That's why I'm not going to continue OfflineIMAP development. I'll continue
> to maintain OfflineIMAP (fixing small bugs, reviewing patches and merging,
> and rolling out new releases), but that's all.
>
> While I keep tracking issues for OfflineIMAP, you should not expect future support.
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
[official Github project][offlineimap].  Provide the following information:
- system/distribution (with version)
- offlineimap version (`offlineimap -V`)
- Python version
- server name or domain
- CLI options
- Configuration file (offlineimaprc)
- pythonfile (if any)
- Logs, error
- Steps to reproduce the error


## The community

* OfflineIMAP's main site is the [project page at Github][offlineimap].
* There is the [OfflineIMAP community's website][website].
* And finally, [the wiki][wiki].


## Requirements & dependencies

* Python v2.7+
* Python v3.4+ ***[STALLED] (experimental: [see known issues](https://github.com/OfflineIMAP/offlineimap/issues?q=is%3Aissue+is%3Aopen+label%3APy3))***
* six (required)
* imaplib2 >= 2.57 (optional)


## Documentation

All current and updated documentation is on the [community's website][website].


### Read documentation locally

You might want to read the documentation locally. Get the sources of the website.
For the other documentation, run the appropriate make target:

```sh
$ ./scripts/get-repository.sh website
$ cd docs
$ make html  # Requires rst2html
$ make man   # Requires a2x (http://asciidoc.org)
$ make api   # Requires sphinx
```
