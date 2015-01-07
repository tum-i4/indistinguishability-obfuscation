import unittest
from itertools import product, chain

from obfusc8.blocks import *

class TestSimBlock(unittest.TestCase):

	def setUp(self):
		self.inputLength = 2
		self.inputs = [Input('x') for _ in range(0, self.inputLength)]
		
		simBlock = SimBlock(self.inputs)
		self.circuit, self.control = simBlock.extractCircuit()
		self.circuit = Circuit(self.circuit, self.control)

	def test_notGate_simulation(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = not test[0]
			result = self.circuit.evaluate([0]+test)
			self.assertEqual(correct, result, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, result, correct))

	def test_andGate_simulation(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = test[0] and test[1]
			result = self.circuit.evaluate([1]+test)
			self.assertEqual(correct, result, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, result, correct))

class TestYBlock(unittest.TestCase):

	def setUp(self):
		self.inputLength = 2
		self.inputs = [Input('x') for _ in range(0, self.inputLength)]

		yBlock = YBlock(self.inputs)
		self.circuit, self.control = yBlock.extractCircuit()
		self.circuit = Circuit(self.circuit, self.control)

	def test_left_switch(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = test[0]
			result = self.circuit.evaluate([0]+test)
			self.assertEqual(correct, result, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, result, correct))

	def test_right_switch(self):
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = test[1]
			result =  self.circuit.evaluate([1]+test)
			self.assertEqual(correct, result, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, result, correct))

class TestSU1(unittest.TestCase):

	def setUp(self):
		self.inputLength = 10
		inputs = [Input('x') for _ in range(0, self.inputLength)]
		su10Block = S_u_1(self.inputLength, inputs)
		output, controls = su10Block.extractCircuit()
		self.circuit = Circuit(output, controls)

	def test_every_position(self):
		for pos in range(self.inputLength):
			ctrlValues = S_u_1.getControlValues(self.inputLength, pos)

			for test in list(product([0,1], repeat=self.inputLength)):
				test = list(test)
				correct = test[pos]
				result = self.circuit.evaluate(ctrlValues+test)
				self.assertEqual(correct, result, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, result, correct))

	def test_getControlValues(self):
		for size in range(2, 100):
			for pos in range(size):
				ctrlValues = S_u_1.getControlValues(size, pos)
				correct = [0]*(pos-1)+[1]+[0]*(size-1-pos) if pos!=0 else [0]*(size-1)
				self.assertEqual(correct, ctrlValues, 'Incorrect control value list')
				
class TestSUV(unittest.TestCase):

	def setUp(self):
		self.inputLength = 10
		inputs = [Input('x') for _ in range(0, self.inputLength)]
		suvBlock = S_u_v(self.inputLength, self.inputLength, inputs)
		outputList, controls = suvBlock.extractCircuit()
		#split controls into lists belonging to one output and consequently to one circuit
		controls = [controls[x:x+self.inputLength-1] for x in xrange(0, self.inputLength**2-self.inputLength, self.inputLength-1)]
		self.circuitList = [Circuit(out, ctrl) for out, ctrl in zip(outputList, controls)]

	def test_every_position(self):
		#use S_u_1 to avoid having to split the control values again
		ctrlValues = [S_u_1.getControlValues(self.inputLength, i) for i in range(self.inputLength)]
		
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			#the ith switch should return the ith bit so the result should be equal to the input
			correct = list(test)
			result = [crc.evaluate(ctrl+test) for crc, ctrl in zip(self.circuitList, ctrlValues)]
			self.assertEqual(correct, result, 'Wrong evaluation on input %s. Was %s instead of %s'%(test, result, correct))

	def test_getControlValues(self):
		correct = list(chain(*[S_u_1.getControlValues(self.inputLength, n) for n in range(self.inputLength)]))
		self.assertEqual(correct, S_u_v.getControlValues(self.inputLength, range(self.inputLength)), 'Incorrect control value list')

class TestUniversalCircuit(unittest.TestCase):

	def setUp(self):
		self.inputLength = 4
		outputLength = 1
		numberOfGates = 5
		self.inputs = [Input('x') for _ in range(0, self.inputLength)]
		
		self.uc = UniversalCircuit(self.inputLength, outputLength, numberOfGates)

	def test_simulate_example_circuit_1(self):
		# -(x0&(x1&(x2&-x3)))
		simuland = Circuit(NotGate(AndGate(self.inputs[0], AndGate(self.inputs[1], AndGate(self.inputs[2], NotGate(self.inputs[3]))))))
		
		simulandCtrlInput = UniversalCircuit.obtainCtrlInput(simuland)
		
		#assert that uc(sCtrlInput+Input) == simuland(Input) on all inputs
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = simuland.evaluate(test)
			result = self.uc.evaluate(simulandCtrlInput+test)
			self.assertEqual(correct, result, 'Simulation not correct on input %s. Was %s instead of %s'%(test, result, correct))

	def test_simulate_example_circuit_2(self):
		# -(x0&x1)&(-x2&x3)
		simuland = Circuit(AndGate(NotGate(AndGate(self.inputs[0], self.inputs[1])), AndGate(NotGate(self.inputs[2]), self.inputs[3])))
		
		simulandCtrlInput = UniversalCircuit.obtainCtrlInput(simuland)
		
		#assert that uc(sCtrlInput+Input) == simuland(Input) on all inputs
		for test in list(product([0,1], repeat=self.inputLength)):
			test = list(test)
			correct = simuland.evaluate(test)
			result = self.uc.evaluate(simulandCtrlInput+test)
			self.assertEqual(correct, result, 'Simulation not correct on input %s. Was %s instead of %s'%(test, result, correct))

	def test_count_reuse_not_allowed(self):
		self.assertTrue(self.uc.countGates(0, False) > self.uc.countGates(0, True), 'not gate number with duplication too big')
		self.assertTrue(self.uc.countGates(1, False) > self.uc.countGates(1, True), 'and gate number with duplication too big')

	def test_calcGates(self):
		self.assertEqual(self.uc.countGates(0), self.uc.calcGates(0), 'wrong calculation of not gate number')
		self.assertEqual(self.uc.countGates(1), self.uc.calcGates(1), 'wrong calculation of and gate number')

if __name__ == '__main__':
	unittest.main()
