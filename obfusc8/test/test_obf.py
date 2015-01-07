import unittest
from itertools import product

from obfusc8.circuit import *
from obfusc8.blocks import UniversalCircuit
from obfusc8.bp import BranchingProgram
from obfusc8.rbp import RandomizedBranchingProgram

from obfusc8.obf import *

class TestFixBP(unittest.TestCase):
	def setUp(self):
		self.inputLength = 2
		outputLength = 1
		numberOfGates = 2
		inputs = [Input("x"+str(x)) for x in range(0, self.inputLength)]
		
		# (-(x0 & x1) & (-x2 & x3)) & ((x4 & x5) & -(x6 & -x7))
		self.circuit = Circuit(NotGate(AndGate(inputs[0], inputs[1])))
		
		uc = UniversalCircuit(self.inputLength, outputLength, numberOfGates)
		bp = BranchingProgram.fromCircuit(uc)
		
		self.fixedBP = fixBP(bp, self.circuit)
	
	def test_fixed_bp_same_functionality(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			circuitResult = self.circuit.evaluate(test)
			bpResult = self.fixedBP.evaluate(test)
			self.assertEqual(circuitResult, bpResult, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, circuitResult, bpResult))

class TestFixRBP(unittest.TestCase):
	def setUp(self):
		self.inputLength = 2
		outputLength = 1
		numberOfGates = 1
		inputs = [Input("x"+str(x)) for x in range(0, self.inputLength)]
		
		# (-(x0 & x1) & (-x2 & x3)) & ((x4 & x5) & -(x6 & -x7))
		self.circuit = Circuit(AndGate(inputs[0], inputs[1]))
		
		uc = UniversalCircuit(self.inputLength, outputLength, numberOfGates)
		rbp = RandomizedBranchingProgram.fromCircuit(uc, 1049, rndMatSize=1)
		
		self.fixedRBP = fixRBP(rbp, self.circuit)

	def test_fixed_rbp_same_functionality(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = self.circuit.evaluate(test)
			rbpResult = self.fixedRBP.evaluate(test)
			self.assertEqual(correct, rbpResult, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, rbpResult, correct))

if __name__ == '__main__':
    unittest.main()
