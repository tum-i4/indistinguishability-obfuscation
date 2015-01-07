"""Building blocks for universal circuit creation

The construction follows a simple procedure which results in UCs of
size in O(k^2 + uk). A detailed description of the algorithm can be
found in [0] or [1].

[0] T. Schneider. "Practical Secure Function Evaluation." MA thesis. 
Friedrich-Alexander-Universität Erlangen-Nürnberg, 2008.
[1] N. Kunze. "A Qualitative Study of Indistinguishability Obfuscation." 
BA thesis. Technische Universität München, 2014.
"""

from circuit import *
import logging

from obfusc8.toposort import toposort_flatten

#------- Blocks ------------

class Block(object):
	"""Super class for all building blocks, should never be instanciated"""
	
	def __init__(self, inputs):
		self.inputs = inputs

	def extractCircuit(self):
		"""Takes the block inputs and generates the correct wirings to the block output(s)"""
		
		pass

class SimBlock(Block):
	"""Simulates one gate of the original circuit.
	
	Has two inputs in0 and in1 which are the inputs to the simulated gate
	and a control input c0 which decides what kind of gate should be simulated.
	c0 = 0 -> NotGate, c0 = 1 -> AndGate
	"""
	def __init__(self, inputs):
		assert(len(inputs) == 2)
		super(SimBlock, self).__init__(inputs)

	def extractCircuit(self):
		c0 = Control()

		#-(in0 & -in1) & -(in0 & -c0) & -(-in0 & c0)

		# a1: -(in0 & -in1)
		a1 = NotGate(AndGate(self.inputs[0], NotGate(self.inputs[1])))
		# a2: -(in0 & -c0)
		a2 = NotGate(AndGate(self.inputs[0], NotGate(c0)))
		# a3: -(-in0 & c0)
		a3 = NotGate(AndGate(NotGate(self.inputs[0]), c0))

		return (AndGate(AndGate(a1, a2), a3), [c0])
	
class YBlock(Block):
	"""Outputs in0 or in1 depending on the value of c0."""
	
	def __init__(self, inputs):
		assert(len(inputs) == 2)
		super(YBlock, self).__init__(inputs)

	def extractCircuit(self):
		c0 = Control()

		#-(-c0 & -in0) & -(c0 & -in1)

		#a1: -(-c0 & -in0)
		a1 = NotGate(AndGate(NotGate(c0), NotGate(self.inputs[0])))
		#a2: -(c0 & -in1)
		a2 = NotGate(AndGate(c0, NotGate(self.inputs[1])))

		return (AndGate(a1, a2), [c0])

class S_u_1(Block):
	"""Outputs one of the u inputs depending on the control values."""
	
	def __init__(self, u, inputs):
		assert(len(inputs) == u)
		self.u = u
		super(S_u_1, self).__init__(inputs)

	def extractCircuit(self):
		if self.u==1: return (self.inputs[0], [])
		#first YBlock takes two inputs as input
		last = YBlock(self.inputs[0:2])
		lastOut, controls = last.extractCircuit()
		for input in self.inputs[2:]:
			#every other YBlock takes first the output of the preceding YBlock and another input
			newInputs = [lastOut, input]
			last = YBlock(newInputs)
			lastOut, ctrl = last.extractCircuit()
			#collect all control inputs
			controls += ctrl
		return lastOut, controls
		
	@staticmethod
	def getControlValues(u, n):
		assert(u>0)
		assert(n<u)
		if u==0: return []
		if n<=0: return (u-1)*[0]
		#to pass input[n] to the output gate the (n-1)th control has to be one
		return [0]*(n-1)+[1]+[0]*(u-1-n)

class S_u_v(Block):
	"""Selection block with u inputs and v outputs.
	
	Each of the outputs can take the value of one of the inputs.
	Naively constructed from v S_u_1 blocks.
	"""
	def __init__(self, u, v, inputs):
		assert(len(inputs) == u)
		self.u = u
		self.v = v
		super(S_u_v, self).__init__(inputs)

	def extractCircuit(self):
		"""!!! Attention! Special case: returns a list of outputs !!!"""
		
		logging.info('Extracting S_u_v Circuit')
		outputs = []
		controls = []
		for i in range(self.v):
			su1 = S_u_1(self.u, self.inputs)
			su1Out, su1Ctrl = su1.extractCircuit()
			#collect outputs and control inputs
			outputs.append(su1Out)
			controls += su1Ctrl
		return (outputs, controls)

	@staticmethod
	def getControlValues(u, nList):
		assert(u>0)
		assert(all(n<u for n in nList))
		ret = []
		for n in nList:
			ret += S_u_1.getControlValues(u, n)

		return ret

class U_k(Block):
	"""Universal Block for k gates.
	
	Has 2k inputs as this is the maximum for a circuit with k gates.
	There are some restrictions on the input structure for each gate.
	"""
	def __init__(self, k, inputs):
		assert(len(inputs) == 2*k)
		self.k = k
		super(U_k, self).__init__(inputs)

	def extractCircuit(self):
		logging.info('Extracting U_K Circuit')
		
		#outputs of each SimGate in order
		outputs = []
		#controls for G1, S21, S21, G2, S31, S31, ...
		controls = []
		for i in range(self.k):
			#left S Block
			sl = S_u_1(i+1, [self.inputs[2*i]]+outputs)
			slOut, slCtrl = sl.extractCircuit()
			#right S Block
			sr = S_u_1(i+1, [self.inputs[2*i+1]]+outputs)
			srOut, srCtrl = sr.extractCircuit()
			#G_i
			sim = SimBlock([slOut,srOut])
			simOut, simCtrl = sim.extractCircuit()

			outputs += [simOut]
			controls += slCtrl+srCtrl+simCtrl

		#only return last output as branching programs only support one output anyways
		return (outputs[-1], controls)

class UCBlock(Block):
	"""Universal Block that lifts the restrictions that the U_k block has on the input structure."""
	
	def __init__(self, u, v, k, inputs):
		#v always 1
		assert(v==1)
		assert(u==len(inputs))
		self.u = u
		self.v = v
		self.k = k
		super(UCBlock, self).__init__(inputs)
	
	def extractCircuit(self):
		logging.info('Extracting UCBlock Circuit')
		
		sin = S_u_v(self.u, 2*self.k, self.inputs)
		sinOut, sinCtrl = sin.extractCircuit()

		u = U_k(self.k, sinOut)
		uOut, uCtrl = u.extractCircuit()

		return uOut, sinCtrl+uCtrl

class UniversalCircuit(Circuit):
	"""Universal circuit for circuit with u inputs, v outputs and k gates.
	
	inputs is the list of inputs for all the circuits that should be simulated by it.
	"""
	def __init__(self, u, v, k):
		self.u = u
		self.v = v
		self.k = k
		inputs = [Input('x') for _ in range(u)]

		logging.info('Generating Universal Circuit with %d inputs, %d outputs and %d gates.', u, v, k)

		self.UC = UCBlock(u, v, k, inputs)
		ucOut, ucCtrls = self.UC.extractCircuit()
		super(UniversalCircuit, self).__init__(ucOut, ucCtrls, inputs)
		
		logging.info('Universal Circuit successfully generated.')
	
	def calcGates(self, type=None):
		"""Calculates the number of gates of a specific type in the UC
		
		type determines if all(None), only NotGates(0) or only AndGates(1) should be counted
		Note that this is the actual number of gates, without duplication
		"""
		if type is None:
			ret = self.calcGates(0) + self.calcGates(1)
		else:
			#s = simBlock gates, y = yblock gates
			if type == 0: s, y = (6, 5)
			elif type == 1: s, y = (5, 3)
			ret = 2*y*self.u*self.k + y*self.k**2 + (s-3*y)*self.k
		return ret
	
	@classmethod
	def obtainCtrlInput(cls, circuit):
		"""Generates value of control inputs to make this universal circuit simulate the input circuit"""
		
		u = len(circuit.inputs)
		k = circuit.countGates()
		
		logging.info('Generating control inputs for circuit')

		#dependencies
		dep = circuit.getDependency()
		logging.debug('Dependencies: %s', dep)

		#topological order
		tOrd = toposort_flatten(dep, sort=True)
		logging.debug('Topological Order: %s', tOrd)

		#datastructure to access gates via id
		gates = circuit.getDict()

		#create lists
		suvList = [-1]*2*k
		slList = [-1]*k
		srList = [-1]*k

		#pythonic ;)
		simList = [[gates[id].getType()] for id in tOrd]

		#traverse each gate in topological order
		counter = 0
		for id in tOrd:
			#for all lists: if don't care simply leave -1
			#slList
			if gates[id].input1.getType() == -1:
				#is input -> connect pos 0 & program S_u_v selektor to pos
				slList[counter] = 0
				suvList[2*counter] = gates[id].input1.pos
			else:
				#is another gate (prior in topological order) -> obtain its position in topo order, selektor value = 1+position
				slList[counter] = 1+tOrd.index(gates[id].input1.id)
			#same for srList
			try:
				if gates[id].input2.getType() == -1:
					srList[counter] = 0
					suvList[2*counter+1] = gates[id].input2.pos
				else:
					srList[counter] = 1+tOrd.index(gates[id].input2.id)
			except AttributeError: pass
			counter += 1

		logging.debug('simList: %s', simList)
		logging.debug('slList: %s', slList)
		logging.debug('srList: %s', srList)
		logging.debug('suvList: %s', suvList)

		#apply mapping to bit values
		suvList = S_u_v.getControlValues(u, suvList)
		slList = [S_u_1.getControlValues(u+1, n) for u, n in zip(range(k), slList)]
		srList = [S_u_1.getControlValues(u+1, n) for u, n in zip(range(k), srList)]

		#unify into one list of input values
		ret = suvList + [a for three in zip(slList, srList, simList) for x in three for a in x]
		return ret
		
	def __str__(self):
		return 'Universal circuit of size %d (for %d inputs, %d output and %d gates)' % \
			(self.countGates(), self.u, self.v, self.k)
	
if __name__ == '__main__':

	from itertools import product

	inputLength = 4
	outputLength = 1
	numberOfGates = 5
	
	uc = UniversalCircuit(inputLength, outputLength, numberOfGates)
	print uc
	
	inputs = [Input('x') for _ in range(0, inputLength)]
	
	# -(x0&x1)&(-x2&x3)
	simuland1 = Circuit(AndGate(NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[2]), inputs[3])))
	s1CtrlInput = UniversalCircuit.obtainCtrlInput(simuland1)
	
	print 'Simuland 1: %s'%simuland1
	print 'S1 Ctrl Input: %s'%s1CtrlInput
	
	
	# -(x0&(x1&(x2&-x3)))
	simuland2 = Circuit(NotGate(AndGate(inputs[0], AndGate(inputs[1], AndGate(inputs[2], NotGate(inputs[3]))))))
	s2CtrlInput = UniversalCircuit.obtainCtrlInput(simuland2)
	
	print 'Simuland 2: %s'%simuland2
	print 'S2 Ctrl Input: %s'%s2CtrlInput
	
	print 'UniversalCircuit testing start...'
	for test in list(product([0,1], repeat=inputLength)):
		test = list(test)
		
		s1Result = simuland1.evaluate(test)
		ucResult1 = uc.evaluate(s1CtrlInput+list(test))
		
		s2Result = simuland2.evaluate(test)
		ucResult2 = uc.evaluate(s2CtrlInput+list(test))
		
		correct = s1Result == ucResult1 and s2Result == ucResult2
		
		print 'Input: %s => S1: %d, UC1: %d, S2: %d, UC2: %d, all good?: %s'%(test, s1Result, ucResult1, s2Result, ucResult2, correct)