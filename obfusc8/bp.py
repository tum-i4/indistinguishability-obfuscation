"""Matrix Branching Programs with 5x5 permutation matrices

This module implements a variant of Matrix Branching Programs that is
close to the ones described by Barrington in [0]. Additionally it 
implements the transformation of logical circuits consisting solely of
AND- and NOT-gates to these MBPs using Barrington's Theorem. The resulting
MBPs make use of numpy arrays as matrices for their speed benefits in
comparison to Sage matrices.

In order to speed up the transformation and to relief memory consumption
the transformation relies on integer IDs instead of permutations / matrices.

[0] D. A. Barrington. "Bounded-width polynomial-size branching programs 
recognize exactly those languages in NC 1." Proceedings of the eighteenth 
annual ACM symposium on Theory of computing. ACM, 1986.
"""

from numpy import array, where, dot
from sys import getsizeof
from os import remove
from itertools import izip
import cPickle
import logging

#---------- Branching Programs ------------------

class BranchingProgram(object):
	"""Branching programs as described by Barrington using 5x5 
	permutation matrices as instructions.
	
	indexList contains all values of inp(i)
	ins0 and ins1 contain all matrices A_i,0 / A_i,1 respectively
	"""
	
	def __init__(self, ins0, ins1, indexList, zeroPerm, onePerm):
		assert(len(ins0) == len(ins1))
		assert(not (zeroPerm==onePerm).all())
		assert(len(indexList) == len(ins0))
		self.length = len(ins0)
		self.ins0 = ins0
		self.ins1 = ins1
		self.indexList = indexList
		self.zeroPerm = zeroPerm
		self.onePerm = onePerm
		
	def evaluate(self, inputs):
		"""Evaluate the branching program for list of input values"""
		
		logging.info('Evaluating branching program for inputs: %s', str(inputs))
		assert(len(inputs) >= max(self.indexList))
		assert(all(bit in (0,1) for bit in inputs))
		
		matrices = ((in1 if inputs[index] else in0) for in0, in1, index in izip(self.ins0, self.ins1, self.indexList))
		result = reduce(dot, matrices)

		ret = -1
		if (result==self.zeroPerm).all(): ret = 0
		if (result==self.onePerm).all(): ret = 1
		logging.info('MBP evaluation result: %d', ret)
		assert(ret != -1)
		return ret
		
	def getInstructionString(self):
		"""Return a human readable string of the instructions"""
	
		strIns0 = map(_matrix2cycle, self.ins0)
		strIns1 = map(_matrix2cycle, self.ins1)
		strList = ["<%d,%s,%s>"%a for a in izip(self.indexList, strIns0, strIns1)]
		return ''.join(strList)
	
	@classmethod
	def fromCircuit(cls, circuit, caching=True):
		"""Return a reverse-normalized (onePerm = identity) branching 
		program as required by the rest of the construction
		
		This implementation uses integer IDs instead of permutation 
		matrices during the generation for performance reasons.
		For a breakdown of how this mappings were created refer to
		the module generate_bp_mappings
		"""
		
		mappings = precalculatedMappings()
		id2perms = precalculatedId2PermList()
		class saveCtr: x=1

		def fastGetIns(gate):
			#Input
			if gate.getType() == -1:
				return ([0], [1], [gate.pos])
			
			#NotGate
			elif gate.getType() == 0:
				id0List, id1List, indexList = fastGetIns(gate.input1)
				id0List[-1] = mappings[0][id0List[-1]]
				id1List[-1] = mappings[0][id1List[-1]]
				id0List[:-1] = [mappings[1][id] for id in id0List[:-1]]
				id1List[:-1] = [mappings[1][id] for id in id1List[:-1]]
				
				return (id0List, id1List, indexList)
				
			elif gate.getType() == 1:
				id0List1, id1List1, indexList1 = fastGetIns(gate.input1)
				a01 = [mappings[2][id] for id in id0List1]
				a11 = [mappings[2][id] for id in id1List1]
				a03 = [mappings[3][id] for id in id0List1]
				a13 = [mappings[3][id] for id in id1List1]
				#'garbage collection'
				id0List1 = None
				id1List1 = None
				
				#write to disk
				if caching==True and getsizeof(a01) > 1000000: #1 mb
					logging.info('caching with size %d...'%getsizeof(a01))
					with open('%d.tmp'%saveCtr.x, 'wb') as output:
						cPickle.dump(a01, output, -1)
						cPickle.dump(a11, output, -1)
						cPickle.dump(a03, output, -1)
						cPickle.dump(a13, output, -1)
					a01 = None
					a11 = None
					a03 = None
					a13 = None
					saveCtr.x += 1
				
				id0List2, id1List2, indexList2 = fastGetIns(gate.input2)
				a02 = [mappings[4][id] for id in id0List2]
				a12 = [mappings[4][id] for id in id1List2]
				a04 = [mappings[5][id] for id in id0List2]
				a14 = [mappings[5][id] for id in id1List2]
				#'garbage collection'
				id0List2 = None
				id1List2 = None
				
				#load from disk
				if a01 is None:
					logging.info('loading...')
					saveCtr.x -= 1
					with open('%d.tmp'%saveCtr.x, 'rb') as input:
						a01 = cPickle.load(input)
						a11 = cPickle.load(input)
						a03 = cPickle.load(input)
						a13 = cPickle.load(input)
					remove('%d.tmp'%saveCtr.x)
				
				return (a01+a02+a03+a04, a11+a12+a13+a14, indexList1+indexList2+indexList1+indexList2)
			
			raise AttributeError
		
		logging.info('Calculating permutation idList')
		id0List, id1List, indexList = fastGetIns(circuit.outputGate)
		
		logging.info('Mapping ids to permutation matrices')
		#instructions = [tuple(id2perms[id] for id in t) for t in idList]
		ins0 = [id2perms[id] for id in id0List]
		ins1 = [id2perms[id] for id in id1List]
		ins0.append(_normalInv())
		ins1.append(_normalInv())
		indexList.append(0)
		return BranchingProgram(ins0, ins1, indexList, _normalInv(), _identity())
		
	@classmethod
	def estimateBPSize(cls, circuit):
		"""Recursively calculates the expected size of the BP belonging to circuit.
		
		Uses the formula
		len_BP(gate) = 	| 1 										if type(gate) = Input
						| len(gate.input)							if type(gate) = NOT
						| 2*len(gate.input1) + 2*len(gate.input2)	if type(gate) = AND
						
		Note that this 'estimation' should indeed be exact.
		"""
		cache = {}
		
		def _estimateBPSize(gate):
			if gate.getType() == -1:
					return 1
			if gate.id in cache:
				ret = cache[gate.id]
			else:
				if gate.getType() == 0:
					ret = _estimateBPSize(gate.input1)
				elif gate.getType() == 1:
					ret = 2*_estimateBPSize(gate.input1)+2*_estimateBPSize(gate.input2)
				cache[gate.id] = ret
			return ret
	
		return _estimateBPSize(circuit.outputGate)+1
	
	def __str__(self):
		return 'Branching Program of length %d, Zero Perm: %s, One Perm: %s' % \
			(self.length, _matrix2cycle(self.zeroPerm), _matrix2cycle(self.onePerm))
			
def _matrix2cycle(permMatrix):
	"""Helper function to get cycle notation of permutation matrix"""
	
	lookedAt = [0]*permMatrix.shape[0]
	ret = ''
	indices = list(where(permMatrix==1)[1])
	
	while not all(lookedAt):
		start = lookedAt.index(0)
		
		if indices[start] != start:		#doesn't point to itself
			ret += '('+str(start)
			
			curr = indices[start]
			while start!=curr:
				ret += str(curr)
				lookedAt[curr] = 1
				curr = indices[curr]
			ret += ')'
			
		lookedAt[start] = 1
	
	if ret=='': ret='e'
	return ret

def _identity(): return array([[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]])	#e
def _normalInv(): return array([[0,0,0,0,1],[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0]])	#(04321)

def precalculatedMappings():
	"""Generated using calculateMappings() from generate_bp_mappings.py"""
	
	return [[1,0,7,8,10,11,14,2,3,21,4,5,29,23,6,15,16,30,33,34,37,9,44,13,45,32,47,41,39,12,17,50,25,18,19,54,51,20,42,28,53,27,38,43,22,24,49,26,58,46,31,36,52,40,35,57,59,55,48,56],[0,2,1,4,3,8,9,16,5,6,22,26,14,15,12,13,7,18,17,32,31,40,10,24,23,41,11,28,27,48,49,20,19,51,54,39,38,43,36,35,21,25,46,37,47,45,42,44,29,30,50,33,57,58,34,56,55,52,53,59],[0,3,4,1,2,6,5,17,9,8,23,27,13,12,15,14,18,7,16,20,19,25,24,10,22,21,28,11,26,49,48,32,31,47,55,36,35,46,39,38,41,40,43,42,51,45,37,33,30,29,50,44,53,52,56,34,54,58,57,59],[0,4,3,2,1,9,8,18,6,5,24,28,15,14,13,12,17,16,7,31,32,41,23,22,10,40,27,26,11,30,29,19,20,44,56,38,39,42,35,36,25,21,37,46,33,45,43,51,49,48,50,47,58,57,55,54,34,53,52,59],[0,5,6,9,8,12,15,19,13,14,25,26,1,4,3,2,20,31,32,35,38,42,21,40,41,37,28,27,11,49,30,39,36,52,44,7,18,10,16,17,43,46,22,23,57,50,24,58,29,48,59,53,55,54,51,33,47,34,56,45],[0,6,5,8,9,13,14,20,12,15,21,28,3,2,1,4,19,32,31,36,39,43,25,41,40,46,26,11,27,29,48,38,35,53,51,17,16,23,18,7,42,37,24,10,58,50,22,57,49,30,59,52,34,56,44,47,33,55,54,45]]

def precalculatedId2PermList():
	"""Generated in generate_bp_mappings.py"""
	
	return [array([[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]]),array([[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1],[1,0,0,0,0]]),array([[0,0,0,0,1],[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0]]),array([[0,0,1,0,0],[0,0,0,0,1],[0,1,0,0,0],[1,0,0,0,0],[0,0,0,1,0]]),array([[0,0,0,1,0],[0,0,1,0,0],[1,0,0,0,0],[0,0,0,0,1],[0,1,0,0,0]]),array([[0,1,0,0,0],[0,0,0,1,0],[1,0,0,0,0],[0,0,0,0,1],[0,0,1,0,0]]),array([[0,0,1,0,0],[1,0,0,0,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,0,1,0]]),array([[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1],[1,0,0,0,0],[0,1,0,0,0]]),array([[0,0,0,0,1],[0,0,0,1,0],[0,1,0,0,0],[1,0,0,0,0],[0,0,1,0,0]]),array([[0,0,0,1,0],[0,0,1,0,0],[0,0,0,0,1],[0,1,0,0,0],[1,0,0,0,0]]),array([[0,0,0,1,0],[1,0,0,0,0],[0,0,1,0,0],[0,1,0,0,0],[0,0,0,0,1]]),array([[1,0,0,0,0],[0,0,0,0,1],[0,0,1,0,0],[0,1,0,0,0],[0,0,0,1,0]]),array([[0,1,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[1,0,0,0,0],[0,0,1,0,0]]),array([[0,0,1,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,1,0,0,0],[1,0,0,0,0]]),array([[0,0,0,0,1],[0,0,0,1,0],[1,0,0,0,0],[0,0,1,0,0],[0,1,0,0,0]]),array([[0,0,0,1,0],[1,0,0,0,0],[0,0,0,0,1],[0,0,1,0,0],[0,1,0,0,0]]),array([[0,0,0,1,0],[0,0,0,0,1],[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0]]),array([[0,1,0,0,0],[0,0,0,1,0],[0,0,0,0,1],[0,0,1,0,0],[1,0,0,0,0]]),array([[0,0,0,0,1],[1,0,0,0,0],[0,0,0,1,0],[0,1,0,0,0],[0,0,1,0,0]]),array([[0,0,0,1,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,1,0,0],[1,0,0,0,0]]),array([[0,0,0,0,1],[0,0,1,0,0],[0,0,0,1,0],[1,0,0,0,0],[0,1,0,0,0]]),array([[0,0,0,1,0],[0,1,0,0,0],[1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1]]),array([[0,0,1,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[1,0,0,0,0]]),array([[0,0,0,0,1],[0,1,0,0,0],[1,0,0,0,0],[0,0,0,1,0],[0,0,1,0,0]]),array([[0,1,0,0,0],[0,0,0,1,0],[0,0,1,0,0],[1,0,0,0,0],[0,0,0,0,1]]),array([[0,0,0,0,1],[1,0,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,1,0,0,0]]),array([[1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,1,0,0,0]]),array([[1,0,0,0,0],[0,1,0,0,0],[0,0,0,1,0],[0,0,0,0,1],[0,0,1,0,0]]),array([[1,0,0,0,0],[0,0,0,1,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,0,1]]),array([[1,0,0,0,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,0,1,0],[0,0,1,0,0]]),array([[1,0,0,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,1,0,0],[0,0,0,1,0]]),array([[0,1,0,0,0],[0,0,0,0,1],[1,0,0,0,0],[0,0,1,0,0],[0,0,0,1,0]]),array([[0,0,1,0,0],[1,0,0,0,0],[0,0,0,1,0],[0,0,0,0,1],[0,1,0,0,0]]),array([[0,0,1,0,0],[0,0,0,0,1],[1,0,0,0,0],[0,0,0,1,0],[0,1,0,0,0]]),array([[0,0,0,1,0],[0,1,0,0,0],[0,0,0,0,1],[1,0,0,0,0],[0,0,1,0,0]]),array([[0,0,0,0,1],[0,0,1,0,0],[1,0,0,0,0],[0,1,0,0,0],[0,0,0,1,0]]),array([[0,0,0,1,0],[1,0,0,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,1,0,0]]),array([[0,0,1,0,0],[1,0,0,0,0],[0,1,0,0,0],[0,0,0,1,0],[0,0,0,0,1]]),array([[0,0,1,0,0],[0,0,0,1,0],[0,1,0,0,0],[0,0,0,0,1],[1,0,0,0,0]]),array([[0,1,0,0,0],[0,0,1,0,0],[0,0,0,0,1],[1,0,0,0,0],[0,0,0,1,0]]),array([[0,0,1,0,0],[0,1,0,0,0],[0,0,0,1,0],[1,0,0,0,0],[0,0,0,0,1]]),array([[0,1,0,0,0],[0,0,0,0,1],[0,0,1,0,0],[0,0,0,1,0],[1,0,0,0,0]]),array([[0,0,0,0,1],[0,1,0,0,0],[0,0,1,0,0],[1,0,0,0,0],[0,0,0,1,0]]),array([[0,0,0,1,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,0,1],[1,0,0,0,0]]),array([[0,0,0,0,1],[0,1,0,0,0],[0,0,0,1,0],[0,0,1,0,0],[1,0,0,0,0]]),array([[1,0,0,0,0],[0,0,1,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,0,1,0]]),array([[0,1,0,0,0],[0,0,1,0,0],[1,0,0,0,0],[0,0,0,1,0],[0,0,0,0,1]]),array([[0,1,0,0,0],[1,0,0,0,0],[0,0,0,1,0],[0,0,1,0,0],[0,0,0,0,1]]),array([[1,0,0,0,0],[0,0,0,1,0],[0,0,1,0,0],[0,0,0,0,1],[0,1,0,0,0]]),array([[1,0,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,1,0,0,0],[0,0,0,0,1]]),array([[1,0,0,0,0],[0,0,0,1,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,1,0,0]]),array([[0,0,0,1,0],[0,0,0,0,1],[0,0,1,0,0],[1,0,0,0,0],[0,1,0,0,0]]),array([[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],[1,0,0,0,0],[0,0,0,0,1]]),array([[0,0,0,0,1],[0,0,1,0,0],[0,1,0,0,0],[0,0,0,1,0],[1,0,0,0,0]]),array([[0,0,1,0,0],[0,0,0,1,0],[1,0,0,0,0],[0,1,0,0,0],[0,0,0,0,1]]),array([[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0],[1,0,0,0,0]]),array([[0,1,0,0,0],[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0]]),array([[0,0,1,0,0],[0,1,0,0,0],[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0]]),array([[0,1,0,0,0],[1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1],[0,0,0,1,0]]),array([[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0]])]
	
if __name__ == '__main__':
	
	#circuit2bp
	from itertools import product
	from circuit import *
	
	inputLength = 8
	inputs = [Input('x') for _ in range(0, inputLength)]
	
	# (-(x0 & x1) & (-x2 & x3)) & ((x4 & x5) & -(x6 & -x7))
	crc = Circuit(AndGate(AndGate(NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[2]), inputs[3])), AndGate(AndGate(inputs[4], inputs[5]),NotGate(AndGate(inputs[6], NotGate(inputs[7]))))))
	print('Circuit: %s'%(crc))
	
	bp = BranchingProgram.fromCircuit(crc)
	print bp
	print 'Branchin Program Instructions:'
	print bp.getInstructionString()
	
	print('BranchinProgram testing start...')
	for test in list(product([0,1], repeat=inputLength)):
		test = list(test)
		circuitResult = crc.evaluate(test)
		bpResult = bp.evaluate(test)
		print 'Input: %s => C: %d, BP: %d, equal?: %s'%(test, circuitResult, bpResult, circuitResult==bpResult)