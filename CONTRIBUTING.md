How to contribute to OfflineIMAP
================================

There are several branches.

`master` represents the current stable branch or what will be the next
sable release.

`next` is where development happens. This is what will be merged into
`master` for the next major release.

Finally, `pu` is a feature branch which hosts crazy features that might or
might not make it into some release. This branch could easily be reset at any
point in time.

To contribute a patch
---------------------

1. Create a feature branch based on `next`:

        $ git checkout next
        $ git branch my-feature
        $ git checkout my-feature

2. Commit your awesome changes:

        $ git commit -m "Add my important feature to the interface"

3. Make a pull request on GitHub or send a patch to the mailing list.

Additional information
----------------------

Other instructions on how to contribute to OfflineIMAP are available at
<http://offlineimap.org/development.html>.
