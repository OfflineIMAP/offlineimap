.. _dco

Developer's Certificate of Origin
=================================

v1.1::

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


Then, you just add a line saying::

  Signed-off-by: Random J Developer <random@developer.example.org>

This line can be automatically added by git if you run the git-commit command
with the ``-s`` option. Signing can made be afterword with ``--amend -s``.

Notice that you can place your own ``Signed-off-by:`` line when forwarding
somebody else's patch with the above rules for D-C-O.  Indeed you are encouraged
to do so.  Do not forget to place an in-body ``From:`` line at the beginning to
properly attribute the change to its true author (see above).

Also notice that a real name is used in the ``Signed-off-by:`` line. Please
don't hide your real name.

If you like, you can put extra tags at the end:

Reported-by
  is used to to credit someone who found the bug that the patch attempts to fix.

Acked-by
  says that the person who is more familiar with the area the patch attempts to
  modify liked the patch.

Reviewed-by
  unlike the other tags, can only be offered by the reviewer and means that she
  is completely satisfied that the patch is ready for application.  It is
  usually offered only after a detailed review.

Tested-by
  is used to indicate that the person applied the patch and found it to have the
  desired effect.

You can also create your own tag or use one that's in common usage such as
``Thanks-to:``, ``Based-on-patch-by:``, or ``Mentored-by:``.


