"""Putting together the different parts of the construction.

This module contains the full construction of an indistinguishability 
obfuscator following the steps as described in [0]. This entails:
0. Input: circuit C with s gates and l inputs, security parameter lambda
1. Generating the correct Universal Circuit UC_sl for s gates and l 
	inputs.
2. Transforming UC_sl to a branching program UBP_sl using Barrington's 
	Theorem.
3. Use the Jigsaw Specifier with some security parameter lambda and the 
	length of UBP_sl as multilinearity parameter and get as output the 
	prime p.
4. Generate the Randomized Branching Program RBP_p(UBP)
5. Encode the Randomized Branching program using the Multilinear Jigsaw
	puzzle.
6. Generate a binary description C' of C and use it to fix all matrices
	that belong to that part of the input. Apply the fixed matrices to
	the ones around them in order to reduce the size of the obfuscation.
	
!!! ATTENTION !!! 
Note again that the MJP component is not working reliably and applying
it will prohibit the correct evaluation of the obfuscation. See mjp.py
for further explanation.
!!! ATTENTION !!! 

[0] S. Garg, C. Gentry, S. Halevi, M. Raykova, A. Sahai, and B. Waters. "Candidate
indistinguishability obfuscation and functional encryption for all circuits." In:
Foundations of Computer Science (FOCS), 2013 IEEE 54th Annual Symposium on.
IEEE. 2013, pp. 40-49.
"""

from copy import deepcopy
from operator import mul
from numpy import dot
from itertools import groupby, izip
import logging

from obfusc8.blocks import UniversalCircuit
from obfusc8.bp import BranchingProgram
from obfusc8.rbp import RandomizedBranchingProgram
from obfusc8.mjp import JigsawPuzzle

counter = 0
def echo(arg):
	"""Simple function to keep track of progress when applying the MJP"""
	
	global counter
	if counter%20 == 0: print counter
	counter += 1
	return arg

class IndistinguishabilityObfuscationGenerator(object):
	"""Complete Indistinguishability Obfuscator as described in the paper
	in Section 4.
	
	Expects as input the inputLenth and the numberOfGates of the circuit
	that shall be obfuscated as well as a secParam. After initialization
	this object can obfuscate any circuits with the correct size and input
	length.
	
	If some intermediate step of the process has been pregenerated it is
	possible to simply load the according member variable (e.g. self.uc)
	with the object. Use cPickle to load and save objects from/on disk.
	"""

	def __init__(self, inputLength, numberOfGates, secParam, rndMatSize=None, mjpDimensionality=None):
		#security parameter needs to be at least as big as the number of gates of the input circuits
		assert(secParam >= numberOfGates)
		
		self.inputLength = inputLength
		self.numberOfGates = numberOfGates
		self.secParam = secParam
		self.rndMatSize = rndMatSize
		self.mjpDimensionality = mjpDimensionality
		
		logging.info('IO Generator initialized')
		logging.info('number of gates s: %d, input lenght l: %d, security parameter lambda: %d'%(numberOfGates, inputLength, secParam))
		logging.info('rbp matrix size: %d, mjp dimensionality: %d'%(rndMatSize, mjpDimensionality))
		
		self.uc = None
		self.bp = None
		self.mjp = None
		self.rbp = None
		
	def generateUC(self):
		"""Universal Circuit generation according to inputs"""
		
		logging.info('Starting UC generation')
		self.uc = UniversalCircuit(self.inputLength, 1, self.numberOfGates)
		logging.info('UC generation successful')
	
	def generateBP(self):
		"""Transform UC to BP. Call UC generation if UC not present."""
	
		if self.uc is None: self.generateUC()
		logging.info('Starting BP generation')
		self.bp = BranchingProgram.fromCircuit(self.uc)
		logging.info('BP generation successful')
	
	def generateMJP(self):
		"""Generate MJP according to inputs. Call BP generation if BP not present"""
	
		if self.bp is None: self.generateBP()
		logging.info('Starting MJP generation')
		self.mjp = JigsawPuzzle(self.bp.length+2, self.secParam, dimensionality=self.mjpDimensionality)
		logging.info('MJP generation successful')
		
	def generateRBP(self):
		"""Randomize BP to obtain RBP. Call MJP generation if MJP not present"""
	
		if self.mjp is None: self.generateMJP()
		logging.info('Starting RBP generation')
		self.rbp = RandomizedBranchingProgram(self.bp, self.mjp.getP(), rndMatSize=self.rndMatSize)
		logging.info('RBP generation successful')
	
	def generateRBPSpecial(self, dim, p):
		"""Generate MJP with a given fixed p. Does NOT call any other step."""
	
		logging.info('Starting RBP generation with fixed p: %d'%p)
		self.rbp = RandomizedBranchingProgram(self.bp, p, rndMatSize=dim)
		logging.info('RBP generation with fixed p successful')
		
	def generateIO(self, circuit):
		"""Fix the RBP with an input circuit and encode the resulting 
		RBP using the MJP to obtain the final obfuscation.
		"""
	
		if self.rbp is None: self.generateRBP()
		logging.info('Starting fixing to get final output')
		fixedRBP = fixRBP(self.rbp, circuit)
		self.io = IndistinguishabilityObfuscation(self.inputLength, fixedRBP, self.mjp)
		logging.info('Fixing successful')
		return self.io
		
	def __str__(self):
		return 'Generator for obfuscations of circuits with %d inputs and %d gates' % (self.inputLength, self.numberOfGates)	
		
class IndistinguishabilityObfuscation(object):
	"""Final obfuscation.
	
	This object is very close to RBPs, with the difference that all
	its elements should be encoded with the MJP. Accordingly the
	evaluation makes use of the zero test.
	"""

	def __init__(self, inputLength, rbp, mjp):
		self.inputLength = inputLength
		
		#copy important attributes
		self.indexList = deepcopy(rbp.indexList)
		self.R_q = deepcopy(mjp.R_q)
		self.pzt = deepcopy(mjp.pzt)
		self.q = deepcopy(mjp.q)
		
		self._applyMJP(rbp, mjp)
		
	def evaluate(self, inputs):
		"""Return the result of the evaluation, namely resultOP-resultDP (Original/Dummy Program)"""
		
		logging.info('Evaluating io with inputs: %s', str(inputs))
		#todo reinstate after fixing matrices?
		assert(len(inputs) == self.inputLength)
		assert(all(bit in (0,1) for bit in inputs))
		
		matricesOP = [(in1 if inputs[index] else in0) for in0, in1, index in izip(self.D_0, self.D_1, self.indexList)]
		resultOP =  reduce(mul, matricesOP, self.s) * self.t

		matricesDP = [(in1 if inputs[index] else in0) for in0, in1, index in izip(self.DP_0, self.DP_1, self.indexList)]
		resultDP = reduce(mul, matricesDP, self.sP) * self.tP
		
		res = resultOP[0] - resultDP[0]

		return self._isZero(res)
	
	def _isZero(self, u):
		"""Test if u is a valid encoding of 0 at the highest level"""
		
		logging.info('Starting zero test.')
		
		#should only be h*e
		v = self.R_q(u*self.pzt)
		
		#test if v is small enough -> has canonical embedding of Euclidean Norm smaller than q^(7/8)
		norm = float(sum([int(a)**2 for a in v.list()]))**(0.5)
		
		ret = norm < (self.q**(7/8.0))
		logging.info('Zero test result: %f < %f => %s'%(norm, self.q**(7/8.0), ret))
		return ret
	
	def _applyMJP(self, rndBP, mjp):
		"""Encode each element of the initial RBP using the functions
		supplied by the MJP. Since this process is very slow, use the
		echo function to keep track of the progress.
		"""
	
		n = rndBP.length
		self.s = rndBP.s.apply_map(lambda z: mjp.encode(z, [0]))
		logging.info('s finished')
		self.t = rndBP.t.apply_map(lambda z: mjp.encode(z, [n+1]))
		logging.info('t finished')
		self.D_0 = [echo(mjp.encodeMatrix(ins, [level+1])) for ins, level in izip(rndBP.D_0, xrange(n))]
		self.D_1 = [echo(mjp.encodeMatrix(ins, [level+1])) for ins, level in izip(rndBP.D_1, xrange(n))]
		logging.info('originalProgram finished')
		
		self.sP = rndBP.sP.apply_map(lambda z: mjp.encode(z, [0]))
		logging.info('sP finished')
		self.tP = rndBP.tP.apply_map(lambda z: mjp.encode(z, [n+1]))
		logging.info('tP finished')
		self.DP_0 = [echo(mjp.encodeMatrix(ins, [level+1])) for ins, level in izip(rndBP.DP_0, xrange(n))]
		self.DP_1 = [echo(mjp.encodeMatrix(ins, [level+1])) for ins, level in izip(rndBP.DP_1, xrange(n))]
		logging.info('dummyProgram finished')
	
	def __str__(self):
		return 'Obfuscation of circuit with input length %d' % self.inputLength

def fixBP(bp, circuit):
	"""Fix a UBP using the binary description of a circuit."""
	
	logging.info('Starting BP fixing')
	ctrlInput = UniversalCircuit.obtainCtrlInput(circuit)
	logging.info('circuit control input: %s'%ctrlInput)
	assert(len(circuit.inputs)+len(ctrlInput) > max(bp.indexList))
	
	newIns0, newIns1, newIndex = fixInstructions(bp.ins0, bp.ins1, bp.indexList, ctrlInput, dot)
	newBP = BranchingProgram(newIns0, newIns1, newIndex, bp.zeroPerm, bp.onePerm)
	logging.info('new BP: %s'%newBP)
	logging.info('BP fixed successfully')
	
	return newBP

def fixRBP(rbp, circuit):
	"""Fix a URBP using the binary description of a circuit."""
	
	logging.info('Starting RBP fixing')
	ctrlInput = UniversalCircuit.obtainCtrlInput(circuit)
	logging.info('circuit control input: %s'%ctrlInput)
	assert(len(circuit.inputs)+len(ctrlInput) > max(rbp.indexList))
	
	newRBP = deepcopy(rbp)
	newRBP.D_0, newRBP.D_1, newIndex = fixInstructions(rbp.D_0, rbp.D_1, rbp.indexList, ctrlInput, mul)
	newRBP.DP_0, newRBP.DP_1, _ = fixInstructions(rbp.DP_0, rbp.DP_1, rbp.indexList, ctrlInput, mul)
	newRBP.indexList = newIndex
	newRBP.length = len(newIndex)
	logging.info('new RBP: %s'%newRBP)
	logging.info('RBP fixed successfully')
	
	return newRBP
		
def fixInstructions(ins0, ins1, indexList, ctrlInput, multiply):
	"""Apply all instructions that are fixed as a result of the control
	input to the next unfixed instruction to their left
	
	This process will not change the result of the fixed (R)BP since
	the evaluator was going to perform these multiplications as well.
	It does however cut down the size of the resulting (R)BP by about
	50% and will actually make it harder to mount any attacks since
	the evaluator has less information.
	"""

	fixingLength = len(ctrlInput)
	
	#get list of lists each lists only contains instructions that either can be fixed or not, order remains the same
	splitted = groupby(izip(indexList, ins0, ins1), lambda x: x[0] < fixingLength)
	
	#check if first group can be fixed and load second one as well if that's the case
	k, group = splitted.next()	
	if k:
		fixed = [(in1 if ctrlInput[index] else in0) for index, in0, in1 in group]
		fixed = reduce(multiply, fixed)
		_, group = splitted.next()
	_, newIns0, newIns1 = map(list, zip(*group))
	if k: 
		newIns0[0] = multiply(fixed, newIns0[0])
		newIns1[0] = multiply(fixed, newIns1[0])
	
	#load all other groups and fix + apply as possible
	for k, group in splitted:
		#can be fixed -> reduce to one matrix and apply to both matrices in instruction to the left
		if k:
			fixed = [(in1 if ctrlInput[index] else in0) for index, in0, in1 in group]
			fixed = reduce(multiply, fixed)
			newIns0[-1] = multiply(newIns0[-1], fixed)
			newIns1[-1] = multiply(newIns1[-1], fixed)
		#no fixing -> only append
		else:
			_, add0, add1 = zip(*group)
			newIns0 += add0
			newIns1 += add1
	
	#remove all indices that where already fixed
	newIndex = filter(lambda x: x >= fixingLength, indexList)
	#correct the index position
	newIndex = [ind-fixingLength for ind in newIndex]
	
	assert(len(newIndex)==len(newIns0))
	
	return (newIns0, newIns1, newIndex)
	
if __name__ == '__main__':
	
	from obfusc8.circuit import Circuit, Input, AndGate, NotGate
	from itertools import product
	
	inputLength = 2
	outputLength = 1
	numberOfGates = 2
	inputs = [Input("x"+str(x)) for x in range(0, inputLength)]
	
	# (-(x0 & x1) & (-x2 & x3)) & ((x4 & x5) & -(x6 & -x7))
	circuit = Circuit(NotGate(AndGate(inputs[0], inputs[1])))
	print circuit
	
	uc = UniversalCircuit(inputLength, outputLength, numberOfGates)
	print uc
	bp = BranchingProgram.fromCircuit(uc)
	print bp
	
	fixedBP = fixBP(bp, circuit)
	print 'After fixing: %s'%fixedBP

	for test in list(product([0,1], repeat=inputLength)):
		test = list(test)
		circuitResult = circuit.evaluate(test)
		bpResult = fixedBP.evaluate(test)
		print('Input: %s => circuit: %d, fixedBP: %d, equal?: %s'%(test, circuitResult, bpResult, circuitResult==bpResult))