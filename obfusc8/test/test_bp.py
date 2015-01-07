import unittest
from itertools import product

from obfusc8.circuit import *
from obfusc8.bp import *

#enable testing of 'private' module member functions, somewhat sloppy style but I prefer it to any alternative
from obfusc8.bp import _matrix2cycle

class TestBranchingProgram(unittest.TestCase):

	def setUp(self):
		self.inputLength = 8
		inputs = [Input("x"+str(x)) for x in range(0, self.inputLength)]
		
		# (-(x0 & x1) & (-x2 & x3)) & ((x4 & x5) & -(x6 & -x7))
		self.circuit = Circuit(AndGate(AndGate(NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[2]), inputs[3])), AndGate(AndGate(inputs[4], inputs[5]),NotGate(AndGate(inputs[6], NotGate(inputs[7]))))))
		
		self.bp = BranchingProgram.fromCircuit(self.circuit)

	def test_estimateBPSize_for_example_circuit(self):
		self.assertEqual(self.bp.length, BranchingProgram.estimateBPSize(self.circuit), 'incorrecet size calculated')

	def test_equality_of_bp_to_circuit(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			circuitResult = self.circuit.evaluate(test)
			bpResult = self.bp.evaluate(test)
			self.assertEqual(circuitResult, bpResult, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, circuitResult, bpResult))

class TestPrecalculatedMappings(unittest.TestCase):

	def setUp(self):
		self.mappings = precalculatedMappings()
		self.id2permList = precalculatedId2PermList()

	def test_precalculated_mappings(self):
		for id, perm in zip(range(len(self.id2permList)), self.id2permList):
			correct = dot(dot(_ni2n(), dot(perm, _normalInv())), _ni2n())
			mappedResult = self.id2permList[self.mappings[0][id]]
			self.assertTrue((correct == mappedResult).all(), 'Mapping 0 not correct on input %s. Was %s instead of %s.'%(perm, mappedResult, correct))
			
			correct = dot(dot(_ni2n(), perm), _ni2n())
			mappedResult = self.id2permList[self.mappings[1][id]]
			self.assertTrue((correct == mappedResult).all(), 'Mapping 0 not correct on input %s. Was %s instead of %s.'%(perm, mappedResult, correct))
			
			correct = dot(dot(_sec2si(), perm), _sec2si())
			mappedResult = self.id2permList[self.mappings[2][id]]
			self.assertTrue((correct == mappedResult).all(), 'Mapping 0 not correct on input %s. Was %s instead of %s.'%(perm, mappedResult, correct))
			
			correct = dot(dot(_special1(), perm), _special1())
			mappedResult = self.id2permList[self.mappings[3][id]]
			self.assertTrue((correct == mappedResult).all(), 'Mapping 0 not correct on input %s. Was %s instead of %s.'%(perm, mappedResult, correct))
			
			correct = dot(dot(_special2(), perm), _special3())
			mappedResult = self.id2permList[self.mappings[4][id]]
			self.assertTrue((correct == mappedResult).all(), 'Mapping 0 not correct on input %s. Was %s instead of %s.'%(perm, mappedResult, correct))
			
			correct = dot(dot(_n2secInv(), perm), _n2sec())
			mappedResult = self.id2permList[self.mappings[5][id]]
			self.assertTrue((correct == mappedResult).all(), 'Mapping 0 not correct on input %s. Was %s instead of %s.'%(perm, mappedResult, correct))

def _identity(): return array([[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]])
def _normal(): return array([[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1],[1,0,0,0,0]]) 	#(01234)
def _normalInv(): return array([[0,0,0,0,1],[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0]]) #(04321)
def _ni2n(): return array([[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0]])		#(14)(23)
def _n2sec(): return array([[1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,1,0,0,0]]) 	#(124)
def _n2secInv(): return array([[1,0,0,0,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,0,1,0],[0,0,1,0,0]]) 	#(142)
def _sec2si(): return array([[1,0,0,0,0],[0,0,1,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,0,1,0]]) 	#(12)(34)
#def _res2n(): return array([[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0]]) 	#(14)(23)
def _special1(): return array([[1, 0, 0, 0, 0],[0, 0, 0, 1, 0],[0, 0, 0, 0, 1],[0, 1, 0, 0, 0],[0, 0, 1, 0, 0]]) #(13)(24)
def _special2(): return array([[1, 0, 0, 0, 0],[0, 1, 0, 0, 0],[0, 0, 0, 0, 1],[0, 0, 1, 0, 0],[0, 0, 0, 1, 0]]) #(243)
def _special3(): return array([[1, 0, 0, 0, 0],[0, 1, 0, 0, 0],[0, 0, 0, 1, 0],[0, 0, 0, 0, 1],[0, 0, 1, 0, 0]]) #(234)

class TestExplicitPermutations(unittest.TestCase):

	def test_matrix2cycle(self):
		a = array([[0,0,1,0,0],[0,1,0,0,0],[1,0,0,0,0],[0,0,0,1,0],[0,0,0,0,1]])
		self.assertEqual(_matrix2cycle(a), '(02)', 'wrong on input %s'%a)
		self.assertEqual('(01234)', _matrix2cycle(_normal()), 'wrong on input %s'%_normal())
		self.assertEqual('e', _matrix2cycle(_identity()), 'wrong on input %s'%_identity())
		self.assertEqual('(04321)', _matrix2cycle(_normalInv()), 'wrong on input %s'%_normalInv())
		self.assertEqual('(14)(23)', _matrix2cycle(_ni2n()), 'wrong on input %s'%_ni2n())
		self.assertEqual('(124)', _matrix2cycle(_n2sec()), 'wrong on input %s'%_n2sec())
		self.assertEqual('(142)', _matrix2cycle(_n2secInv()), 'wrong on input %s'%_n2secInv())
		self.assertEqual('(12)(34)', _matrix2cycle(_sec2si()), 'wrong on input %s'%_sec2si())
		self.assertEqual('(13)(24)', _matrix2cycle(_special1()), 'wrong on input %s'%_special1())
		self.assertEqual('(243)', _matrix2cycle(_special2()), 'wrong on input %s'%_special2())
		self.assertEqual('(234)', _matrix2cycle(_special3()), 'wrong on input %s'%_special3())

if __name__ == '__main__':
	unittest.main()
