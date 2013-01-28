# Copyright 2013 Eygene A. Ryabinkin
# Functions to perform stack tracing (for multithreaded programs
# as well as for single-threaded ones).

import sys
import threading
import traceback


def dump(out):
	""" Dumps current stack trace into I/O object 'out' """
	id2name = {}
	for th in threading.enumerate():
		id2name[th.ident] = th.name
	n = 0
	for i, stack in sys._current_frames().items():
		out.write ("\n# Thread #%d (id=%d), %s\n" % \
		  (n, i, id2name[i]))
		n = n + 1
		for f, lno, name, line in traceback.extract_stack (stack):
			out.write ('File: "%s", line %d, in %s' % \
			  (f, lno, name))
			if line:
				out.write (" %s" % (line.strip()))
			out.write ("\n")
