import unittest
from itertools import product
from operator import mul

from obfusc8.circuit import *
from obfusc8.rbp import *

#enable testing of 'private' module member functions, somewhat sloppy style but I prefer it to any alternative
from obfusc8.rbp import _generateRs, _generateAlphas, _generateVectors

class TestRandomizedBranchingProgram(unittest.TestCase):

	def setUp(self):
		self.inputLength = 4
		inputs = [Input('x') for _ in range(0, self.inputLength)]
		self.crc = Circuit(AndGate(NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[2]), inputs[3])))
		self.rbp = RandomizedBranchingProgram.fromCircuit(self.crc, 1049)

	def test_rbp_evaluates_equal_to_circuit(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = self.crc.evaluate(test)
			rbpResult = self.rbp.evaluate(test)
			self.assertEqual(correct, rbpResult, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, rbpResult, correct))

class TestGenerateRs(unittest.TestCase):

	def setUp(self):
		self.m = 10
		self.testListLength = 100
		self.ring = Integers(random_prime(1000, lbound=71))

	def test_generateRs_constraints(self):
		rGen = _generateRs(self.ring, self.m)
		fullList = [mat for _ in range(self.testListLength) for mat in rGen.next()]
		reduced = reduce(mul, fullList)
		shortcut = fullList[0]*fullList[-1]
		self.assertEqual(reduced, shortcut, 'Constraint on _generateRs does not hold. \nfullList: %s \nReduced: %s, Shortcut: %s'%(fullList, reduced, shortcut))

class TestGenerateAlphas(unittest.TestCase):

	def setUp(self):
		self.repetitions = 100
		self.ring = Integers(random_prime(1000, lbound=71))
		self.indexListLength = 100
		self.indexListMax = 25

	def test_alpha_constraints(self):
		ints = IntegerRing()
		for _ in range(self.repetitions):
			#generate indexList at random
			indexList = [ints.random_element(self.indexListMax) for _ in range(self.indexListLength)]
			a, aP = _generateAlphas(len(indexList), indexList, self.ring)
			for i in range(max(indexList) + 1):
				aF = [alpha for alpha, index in zip(a, indexList) if index == i]
				aPF = [alpha for alpha, index in zip(aP, indexList) if index == i]
				productAF = reduce(mul, aF, self.ring(1))
				productAPF = reduce(mul, aPF, self.ring(1))
				self.assertEqual(productAF, productAPF, 
					'Product of alphas not equal for index %d. First product: %d, second product: %d'%(i, productAF, productAPF))
	
class TestGenerateVectors(unittest.TestCase):

	def setUp(self):
		self.repetitions = 100
		self.ring = Integers(random_prime(1000, lbound=71))
		
	def test__generateVectors_constraints(self):
		for _ in range(self.repetitions):
			sS, tS, sPS, tPS = _generateVectors(self.ring)
			#compute scalar product
			productS = sum([a*b for a, b in zip(sS, tS)])
			productPS = sum([a*b for a, b in zip(sPS, tPS)])
			self.assertEqual(productS, productPS, 'Generate vectors do not heed constraint. ProductS: %d, productSP: %d'%(productS, productPS))

if __name__ == '__main__':
    unittest.main()
