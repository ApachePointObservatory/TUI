#!/usr/local/bin/python
"""
An iterator over multiple lists or other collections.
Stops at the end of the shortest list.

From Daniel Dittmar in a discussion "Why I think range is a wart"
"""
class MultiListIter:
	def __init__(self, *lists):
		self.iters = map(iter, lists)
	
	def __iter__(self):
		return self
	
	def next(self):
		return [elem.next() for elem in self.iters]


if __name__ == "__main__":
	print "MultiListIter example"
	a = range(5)
	b = [x**2 for x in a]
	print "a = %r" % a
	print "b = %r" % b
	print "for res in MultiListIter(a, b):"
	for res in MultiListIter(a, b):
		print "\t%r" % (res,)