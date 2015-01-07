"""Logical circuits consisting of AND- and NOT-gates.

This module provides an implementation for simple logical circuits 
consisting solely of AND- and NOT-gates. A complete circuit consists 
of a container object of type Circuit which recursively references the
gates and inputs that the circuit consists of. In order to facilitate
the transformation to Matrix Branching Programs using Barrington's Theorem,
each class provides a variety of functionalities.
"""

import logging
from itertools import count

#------------ Circuit --------------------------

class Circuit(object):
	"""Boolean Circuits consisting of AND and NOT gates
	
	This is a container class that provides all necessary functionality
	that external modules require for their work. It holds a reference
	to the output gate of the circuit, all other gates and inputs of the
	circuit are referenced in a recursive manner.
	"""
	
	def __init__(self, outputGate, ctrlInputs=[], inputs=[]):
		logging.info('Creating circuit')
		
		self.outputGate = outputGate
		self.controls = ctrlInputs
		self.inputs = inputs
		
		#contains [#NotGates, #AndGates, #NotGates (reuse allowed), #AndGates (reuse allowed)]
		self.numGates = [None, None, None, None]
		
		#if no inputs were supplied, find them by depth first search
		if inputs==[]:
			seen = set()
			seen_add = seen.add
			#make found inputs unique
			self.inputs = [ x for x in self.outputGate.getInputs() if not (x in seen or seen_add(x))]
		
		#calculate the controls positions
		[ctrl.setPos(pos) for ctrl, pos in zip(self.controls, range(len(self.controls)))]
		[inp.setPos(pos) for inp, pos in zip(self.inputs, range(len(self.controls), len(self.controls)+len(self.inputs)))]
	
	def evaluate(self, inputValues):
		"""Evaluate the circuit for list of input values"""
		
		logging.info('Evaluating circuit with inputs: %s', str(inputValues))
		assert(len(self.controls+self.inputs) == len(inputValues))
		assert(all(bit in (0,1) for bit in inputValues))
		
		map(Input.set, self.controls+self.inputs, inputValues)
		ret = self.outputGate.evaluate()
		
		logging.info('Circuit evaluation result: %d', ret)
		return ret
	
	def countGates(self, type=None, reuseAllowed=True):
		"""Recursively count number of gates in the circuit
		
		type determines if all(None), only NotGates(0) or only AndGates(1) should be counted
		reuseAllowed determines if the output of a gate can be used by multiple other gates (True) or if they should be duplicated each time (False)
		"""
		if type is None:
			ret = self.countGates(0)+self.countGates(1)
		else:
			#calculate if necessary
			if self.numGates[2*reuseAllowed+type] is None:
				if reuseAllowed:
					allGateTypes = [gate.getType() for gate in self.getDict().values()]
					self.numGates[2+type] = allGateTypes.count(type)
				else:
					self.numGates[type] = self.outputGate.countGates(type)	
			ret = self.numGates[2*reuseAllowed+type]
		return ret
	
	def getDepth(self):
		"""Calculate the depth (= longest path from input to output) of the circuit"""
	
		return self.outputGate.getDepth()
	
	def getDependency(self):
		"""Generate dictionary with gate dependencies
		
		Gate A depends on another gate B iff A uses the value of B as input.
		"""
		
		return dict(self.outputGate.getDependency())
		
	def getDict(self):
		"""Return dictionary for quick gate access, keys are the gateIDs"""
		
		return dict(self.outputGate.getDict())
	
	def __str__(self):
		return str(self.outputGate)
		
class Gate(object):
	"""Super class for all gates, should never be instantiated"""

	newid = count().next
	
	def __init__(self):
		#generate unique ID for each gate
		self.id = Gate.newid()
		self.numGates = [None, None]
	
	def __repr__(self):
		return self.__str__()

class Input(Gate):
	"""Regular Inputs, can have values 0 or 1"""
	
	def __init__(self, name):
		self.name = name
		self.set(0)
		super(Input, self).__init__()
		
	def setPos(self, pos):
		self.pos = pos
	
	def set(self, value):
		assert(value in (0,1))
		self.value = value
	
	def evaluate(self):
		return self.value
	
	def countGates(self, type):
		return 0
		
	def getDict(self):
		return []
		
	def getDepth(self):
		return 0
		
	def getInputs(self, ctrl=False):
		if ctrl: return []
		return [self]
	
	def getType(self):
		return -1
	
	def __str__(self):
		try:
			return '%s%d'%(self.name, self.pos)
		except AttributeError:
			return str(self.name)
		
class Control(Input):
	"""Control inputs for Universal Circuit
	
	These inputs belong to the binary circuit description that a UC
	expects as part of its input and determine the behavior of the UC.
	"""
	
	def __init__(self):
		super(Control, self).__init__("c")
		self.name += str(self.id)
	
	def getInputs(self, ctrl=False):
		if ctrl: return [self]
		return []
	
class NotGate(Gate):
	"""Not Gate, outputs not(input)"""
	
	def __init__(self, input):
		self.input1 = input
		super(NotGate, self).__init__()
		
	def evaluate(self):
		return 1 - self.input1.evaluate()
	
	def countGates(self, type):
		if self.numGates[type] is None:
			self.numGates[type] = (1 if type==0 else 0)+self.input1.countGates(type)
		return self.numGates[type]
	
	def getDependency(self):
		if self.input1.getType() == -1: 	#is an Input
			return [(self.id, set())]
		return self.input1.getDependency()+[(self.id, {self.input1.id})]
		
	def getDict(self):
		return self.input1.getDict()+[(self.id, self)]
		
	def getType(self):
		"""Type used for simulation block control input"""
		
		return 0
	
	def getInputs(self, ctrl=False):
		return self.input1.getInputs(ctrl)
	
	def getDepth(self):
		return 1+self.input1.getDepth()
	
	def __str__(self):
		return "-"+str(self.input1)
	
class AndGate(Gate):
	"""And Gate, outputs (input1 and input2)"""
	
	def __init__(self, input1, input2):
		self.input1 = input1
		self.input2 = input2
		super(AndGate, self).__init__()
		
	def evaluate(self):
		return self.input1.evaluate() and self.input2.evaluate()
	
	def countGates(self, type):
		if self.numGates[type] is None:
			self.numGates[type] = (1 if type==1 else 0)+self.input1.countGates(type)+self.input2.countGates(type)
		return self.numGates[type]
	
		if type in (None, 1): ret = 1
		else: ret = 0
		return ret+self.input1.countGates(type)+self.input2.countGates(type)
		
	def getDependency(self):
		dependsOn = []
		ret = []
		if self.input1.getType() != -1:		#is not an Input
			dependsOn.append(self.input1.id)
			ret += self.input1.getDependency()
		if self.input2.getType() != -1:		#is not an Input
			dependsOn.append(self.input2.id)
			ret += self.input2.getDependency()
		return ret+[(self.id, set(dependsOn))]
		
	def getDict(self):
		return self.input1.getDict() + self.input2.getDict() + [(self.id, self)]
		
	def getType(self):
		"""Type used for simulation block control input"""
		
		return 1
		
	def getInputs(self, ctrl=False):
		return self.input1.getInputs(ctrl)+self.input2.getInputs(ctrl)
		
	def getDepth(self):
		return 1+max(self.input1.getDepth(), self.input2.getDepth())
	
	def __str__(self):
		return "("+str(self.input1)+"&"+str(self.input2)+")"
	
if __name__ == '__main__':
	
	from itertools import product
	
	inputLength = 4
	inputs = [Input('x') for _ in range(0, inputLength)]
	
	# -(x0&x1)&(-x2&x3)
	a = Circuit(AndGate(NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[2]), inputs[3])))
	print 'Circuit: %s'%(a)
	
	#countGates
	print 'Number of Gates: %d'%(a.countGates())

	for test in list(product([0,1], repeat=inputLength)):
		test = list(test)
		circuitResult = a.evaluate(test)
		correct = (not (test[0] and test[1]) and (not test[2] and test[3]))
		print 'Input: %s => C: %d, Correct: %d, equal?: %s'%(test, circuitResult, correct, circuitResult==correct)