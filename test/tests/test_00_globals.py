#!/usr/bin/env python
# Copyright 2013 Eygene A. Ryabinkin

from offlineimap import globals
import unittest

class Opt:
	def __init__(self):
		self.one = "baz"
		self.two = 42
		self.three = True


class TestOfflineimapGlobals(unittest.TestCase):

	@classmethod
	def setUpClass(klass):
		klass.o = Opt()
		globals.set_options (klass.o)

	def test_initial_state(self):
		for k in self.o.__dict__.keys():
			self.assertTrue(getattr(self.o, k) ==
			  getattr(globals.options, k))

	def test_object_changes(self):
		self.o.one = "one"
		self.o.two = 119
		self.o.three = False
		return self.test_initial_state()

	def test_modification(self):
		with self.assertRaises(AttributeError):
			globals.options.two = True

	def test_deletion(self):
		with self.assertRaises(RuntimeError):
			del globals.options.three

	def test_nonexistent_key(self):
		with self.assertRaises(AttributeError):
			a = globals.options.nosuchoption

	def test_double_init(self):
		with self.assertRaises(ValueError):
			globals.set_options (True)


if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(TestOfflineimapGlobals)
	unittest.TextTestRunner(verbosity=2).run(suite)
