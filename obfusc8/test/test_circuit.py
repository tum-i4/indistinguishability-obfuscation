import unittest
from itertools import product

from obfusc8.circuit import *

class TestCircuit(unittest.TestCase):

	def setUp(self):
		self.inputLength = 4
		self.inputs = [Input('x') for _ in range(0, self.inputLength)]
		self.a1 = AndGate(self.inputs[0], self.inputs[1])
		self.n1 = NotGate(self.a1)
		self.n2 = NotGate(self.inputs[2])
		self.a2 = AndGate(self.n2, self.inputs[3])
		self.a3 = AndGate(self.n1, self.a2)
		self.circuit =  Circuit(self.a3)

	def tearDown(self):
		self.inputLength = None
		self.inputs = None
		self.c1 = None

	def test_init(self):
		self.assertEqual(self.inputs, self.circuit.inputs, 'input detection broken')

	def test_countGates_basic(self):
		self.assertEqual(5, self.circuit.countGates(), 'wrong gate count')

	def test_countGates_not(self):
		self.assertEqual(2, self.circuit.countGates(0), 'wrong not gate count')

	def test_countGates_and(self):
		self.assertEqual(3, self.circuit.countGates(1), 'wrong and gate count')

	def test_countGates_add(self):
		self.assertEqual(self.circuit.countGates(), self.circuit.countGates(0)+self.circuit.countGates(1), 'complete gate count unequal to not + and Gates')

	def test_evaluate(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = (not (test[0] and test[1]) and (not test[2] and test[3]))
			self.assertEqual(correct, self.circuit.evaluate(test), 'Wrong evaluation on input %s. Was %s instead of %s'%(test, self.circuit.evaluate(test), correct))

	def test_getDependency(self):
		resultDict = {self.a3.id: set([self.n1.id, self.a2.id]), self.n1.id:set([self.a1.id]), self.a2.id: set([self.n2.id]), self.a1.id: set([]), self.n2.id: set([])}
		self.assertEqual(resultDict, self.circuit.getDependency(), 'wrong dependency dictionary')

	def test_getDepth(self):
		self.assertEqual(3, self.circuit.getDepth(), 'incorrect depth on example circuit')

	def test_getDict(self):
		resultDict = {self.a3.id: self.a3, self.a2.id: self.a2, self.a1.id: self.a1, self.n2.id: self.n2, self.n1.id: self.n1}
		self.assertEqual(resultDict, self.circuit.getDict(), 'wrong mapping dict')

	def test_str(self):
		self.assertEqual('(-(x0&x1)&(-x2&x3))', str(self.circuit), 'string conversion does not match')

class TestInput(unittest.TestCase):

	def setUp(self):
		self.input = Input('x0')

	def tearDown(self):
		self.input = None

	def test_value_zero_after_init(self):
		self.assertEqual(0, self.input.evaluate(), 'initial value not zero')

	def test_str_returns_name(self):
		self.assertEqual('x0', str(self.input))

	def test_countGates_returns_zero(self):
		self.assertEqual(0, self.input.countGates(None), 'countGates does not return zero')

	def test_getDepth_returns_zero(self):
		self.assertEqual(0, self.input.getDepth(), 'getDepth does not return zero')

	def test_getType_correctness(self):
		self.assertEqual(-1, self.input.getType(), 'getType does not return -1')

	def test_set_and_evaluate(self):
		self.input.set(1)
		self.assertEqual(1, self.input.evaluate(), 'evaluation with value set to 1 does not return 1')
		self.input.set(0)
		self.assertEqual(0, self.input.evaluate(), 'evaluation with value set to 0 does not return 0')

class TestNotGate(unittest.TestCase):

	def setUp(self):
		self.input = Input('x0')
		self.gate = NotGate(self.input)

	def tearDown(self):
		self.gate = None

	def test_init(self):
		self.assertEqual(self.input, self.gate.input1, 'input not assigned to input1')

	def test_str(self):
		self.assertEqual('-x0', str(self.gate), 'string conversion does not match')

	def test_countGates_with_type_zero(self):
		self.assertEqual(1, self.gate.countGates(0), 'countGates with type 0 incorrect')

	def test_countGates_with_type_one(self):
		self.assertEqual(0, self.gate.countGates(1), 'countGates with type 1 incorrect')

	def test_evaluate(self):
		self.input.set(0)
		self.assertEqual(1, self.gate.evaluate(), 'Wrong evaluation on input [0]. Was %s instead of 1'%self.gate.evaluate())
		self.input.set(1)
		self.assertEqual(0, self.gate.evaluate(), 'Wrong evaluation on input [1]. Was %s instead of 0'%self.gate.evaluate())

	@unittest.skip('not important')
	def test_getDependency(self):
		# and_gate = AndGate(input1, input2)
		# self.assertEqual(expected, and_gate.getDependency())
		assert False # TODO: implement your test here

	def test_getDepth(self):
		self.assertEqual(1, self.gate.getDepth())

	@unittest.skip('not important')
	def test_getDict(self):
		# and_gate = AndGate(input1, input2)
		# self.assertEqual(expected, and_gate.getDict())
		assert False # TODO: implement your test here

	def test_getInputs(self):
		self.assertEqual([self.input], self.gate.getInputs(), 'getInputs result not identical to initial inputs')

	def test_getType(self):
		self.assertEqual(0, self.gate.getType())

class TestAndGate(unittest.TestCase):

	def setUp(self):
		self.inputLength = 2
		self.inputs = [Input('x') for _ in range(0, self.inputLength)]
		self.gate = AndGate(self.inputs[0], self.inputs[1])
		self.circuit = Circuit(self.gate)

	def tearDown(self):
		self.inputLength = None
		self.inputs = None
		self.gate = None

	def test_init(self):
		self.assertEqual(self.inputs[0], self.gate.input1, 'left input not assigned to input1')
		self.assertEqual(self.inputs[1], self.gate.input2, 'right input not assigned to input2')

	def test_str(self):
		self.assertEqual('(x0&x1)', str(self.gate), 'string conversion does not match')

	def test_countGates_with_type_zero(self):
		self.assertEqual(0, self.gate.countGates(0), 'countGates with type 0 incorrect')

	def test_countGates_with_type_one(self):
		self.assertEqual(1, self.gate.countGates(1), 'countGates with type 1 incorrect')

	def test_evaluate(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = (test[0] and test[1])
			self.assertEqual(correct, self.circuit.evaluate(test), 'Wrong evaluation on input %s. Was %s instead of %s'%(test, self.circuit.evaluate(test), correct))

	@unittest.skip('not important')
	def test_getDependency(self):
		# and_gate = AndGate(input1, input2)
		# self.assertEqual(expected, and_gate.getDependency())
		assert False # TODO: implement your test here

	def test_getDepth(self):
		self.assertEqual(1, self.gate.getDepth())

	@unittest.skip('not important')
	def test_getDict(self):
		# and_gate = AndGate(input1, input2)
		# self.assertEqual(expected, and_gate.getDict())
		assert False # TODO: implement your test here

	def test_getInputs(self):
		self.assertEqual(self.inputs, self.gate.getInputs(), 'getInputs result not identical to initial inputs')

	def test_getType(self):
		self.assertEqual(1, self.gate.getType())

if __name__ == '__main__':
	unittest.main()
