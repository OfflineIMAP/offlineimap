Systemd units
=============

These unit files are meant to be used in the user session. You may drop them
into `${XDG_DATA_HOME}/systemd/user` followed by `systemctl --user
daemon-reload` to have systemd aware of the unit files.

These files are meant to be triggered either manually using `systemctl --user
start offlineimap.service` or by enabling the timer unit using `systemctl
--user enable offlineimap.timer`. Additionally, specific accounts may be
triggered by using `offlineimap@myaccount.timer` or
`offlineimap@myaccount.service`.

These unit files are installed as being enabled via a `mail.target` unit which
is intended to be a catch-all for mail-related unit files. A simple
`mail.target` file is also provided.
