# gpg-offlineimap

Python bindings for offlineimap to use gpg instead of storing cleartext passwords

Author: Lorenzo G.
[GitHub](https://github.com/lorenzog/gpg-offlineimap)

## Quickstart

Requirements: a working GPG set-up. Ideally with gpg-agent. Should work
out of the box on most modern Linux desktop environments.

 1. Enable IMAP in gmail (if you have two factor authentication, you
    need to create an app-specific password)

 2. Create a directory `~/Mail`

 3. In `~/Mail`, create a password file `passwords-gmail.txt`. Format:
    `account@gmail.com password`. Look at the example file in this
    directory.

 4. **ENCRYPT** the file: `gpg -e passwords-gmail.txt`. It should create
    a file `passwords-gmail.txt.gpg`. Check you can decrypt it: `gpg -d
    passwords-gmail.txt.gpg`: it will ask you for your GPG password and
    show it to you.

 5. Use the file  `offlineimaprc.sample` as a sample for your own
    `.offlineimaprc`; edit it by following the comments. Minimal items
    to configure: the `remoteuser` field and the `pythonfile` parameter
    pointing at the `offlineimap.py` file in this directory.

 6. Run it: `offlineimap`. It should ask you for your GPG passphrase to
    decrypt the password file.

 7. If all works well, delete the cleartext password file.


