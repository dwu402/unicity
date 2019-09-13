# tests various combinations
from glob import glob
import os

def run_one(test):
	pass

def assemble_tests():
	tests = [1.]
	return tests

def run_all_tests():

	tests = assemble_tests()
	for test in tests:
		try:
			fls0 = glob('./*')
			run_one(test)
			newfls = list(set(glob('./*')) - set(fls0))
			for fl in newfls: 
				os.remove(fl)
			print('test {:s}: passed'.format(test[0]))
		except:
			print('test {:s}: FAILED'.format(test[0]))

if __name__ == "__main__":
	run_all_tests()