"""Randomized Branching Programs

This module implements Randomized Branching Programs as described
in Section 4.1 of the original paper. Sage provides an implementation
of Z_p and matrices over Z_p. There are various helper functions in
order to facilitate the generation.
"""

from sage.all import *
from operator import mul
from itertools import izip, imap
import logging

from obfusc8.bp import BranchingProgram

class RandomizedBranchingProgram(object):
	"""Randomized Branching Programs as described in Section 4.1 of
	the original paper.
	
	This should be very close to the original description. In order to
	improve performance it is possible to set the size of the random
	matrices (m in the original paper) to a constant instead of making
	it dependent on the length of the input Branching Program.
	"""

	def __init__(self, branchingProgram, p, rndMatSize=None):
		logging.info('Creating randomized branching program')

		# ------------ setup ------------------
		self.p = p
		self.ring = Integers(p)
		self.length = branchingProgram.length
		self.indexList = branchingProgram.indexList
		self.m = self.__getM(rndMatSize)

		#shorthands
		n = self.length
		m = self.m
		ring = self.ring

		# ----------- generate alphas -------------
		logging.info('Generating Alphas')
		a0, a0P = _generateAlphas(n, self.indexList, ring)
		a1, a1P = _generateAlphas(n, self.indexList, ring)

		#----------- generate D, D' -------------------
		
		#some speed trickery, this method was fastest in during testing
		def genDMatrix(ins, alpha): 
			ret = diagonal_matrix(ring, _randomElements(ring, 2 * m)+[0]*5)
			ret[-5:,-5:] = alpha*matrix(ins)
			return ret
		
		#D_0 is a list of all D_i0
		logging.info('Generating D_0')
		D_0 = imap(genDMatrix, branchingProgram.ins0, a0)
		
		#and D_1 of all D_i1
		logging.info('Generating D_1')
		D_1 = imap(genDMatrix, branchingProgram.ins1, a1)
		
		#again trying to speed things up
		def genDPMatrix(alpha):
			return diagonal_matrix(ring, _randomElements(ring, 2 * m)+[alpha]*5)
		
		#same for D' with Identity + a0/1p
		logging.info('Generating DP_0')
		DP_0 = imap(genDPMatrix, a0P)
		
		logging.info('Generating DP_1')
		DP_1 = imap(genDPMatrix, a1P)

		#------------- generate s, t, s', t' ----------------------------------
		
		logging.info('Generating s,t,sP,tP')
		sS, tS, sPS, tPS = _generateVectors(ring)

		s = vector(ring, [ring(0)] * m + _randomElements(ring, m) + sS)
		sP = vector(ring, [ring(0)] * m + _randomElements(ring, m) + sPS)

		t = vector(ring, _randomElements(ring, m) + [ring(0)] * m + tS).column()
		tP = vector(ring, _randomElements(ring, m) + [ring(0)] * m + tPS).column()

		#------------- generate and apply R_0, ... R_n -------------------------
		
		#third time performance optimizations
		def mul3(ins0, ins1): 
			Ri1, RiInv = rGen.next()
			return (Ri1 * ins0 * RiInv, Ri1 * ins1 * RiInv)
		
		#main program
		logging.info('Applying random matrices to original program')
		
		rGen = _generateRs(ring, m)
		_, R0Inv = rGen.next()
		self.s = s * R0Inv
		self.D_0, self.D_1 = map(list, zip(*imap(mul3, D_0, D_1)))
		Rn, _ = rGen.next()
		self.t = Rn * t
				
		#dummy program
		logging.info('Applying random matrices to dummy program')
		
		rGen = _generateRs(ring, m)
		_, R0Inv = rGen.next()
		self.sP = sP * R0Inv
		self.DP_0, self.DP_1 = map(list, zip(*imap(mul3, DP_0, DP_1)))
		Rn, _ = rGen.next()
		self.tP = Rn * tP	
		
	@classmethod
	def fromCircuit(cls, circuit, p, rndMatSize=None):
		"""Create a RBP directly with a circuit input"""
		
		return cls(BranchingProgram.fromCircuit(circuit), p, rndMatSize)

	def evaluate(self, inputs):
		"""Evaluate the RBP for list of input values"""
		
		logging.info('Evaluating rbp with inputs: %s', str(inputs))
		assert(len(inputs) >= max(self.indexList))
		assert(all(bit in (0,1) for bit in inputs))
		
		matricesOP = ((in1 if inputs[index] else in0) for in0, in1, index in izip(self.D_0, self.D_1, self.indexList))
		resultOP =  reduce(mul, matricesOP, self.s) * self.t

		matricesDP = ((in1 if inputs[index] else in0) for in0, in1, index in izip(self.DP_0, self.DP_1, self.indexList))
		resultDP = reduce(mul, matricesDP, self.sP) * self.tP
		
		#Result of Original Program - Result of Dummy Program should be 0
		if (resultOP[0] - resultDP[0]) == 0: ret = 1
		else: ret = 0
		logging.info('rbp evaluation result: %d', ret)
		return ret
	
	def __getM(self, size):
		"""Choose m according to size.
		
		size = None -> use the standard way described in the paper.
		otherwise use size directly
		"""
		
		ret = -1
		if size is None:
			ret = 2*self.length + 5
		else:
			assert(size >= 0)
			#use constant for reasonable runtime
			ret = size
		assert(ret != -1)
		return ret
	
	def __str__(self):
		return 'Randomized Branching Program of length %d over ring modulo %d' % (self.length, self.p)

def _generateRs(ring, m):
	"""Return a tuple with two (semi)random matrices of size 2*m+5 
	over the ring. The first matrix is the inverse of the second matrix 
	that was handed out in the previous round. The second matrix is new and random.
	"""
	
	assert(m>=0)
	
	old = random_matrix(ring, 2 * m + 5)
	
	while not old.is_invertible():
		old = random_matrix(ring, 2 * m + 5)
	
	while True:
		new = random_matrix(ring, 2 * m + 5)
		while not new.is_invertible():
			new = random_matrix(ring, 2 * m + 5)
		newInv = new.inverse()
		#print 'yield'
		yield (old, newInv)
		old = new

def _generateAlphas(n, indexList, ring):
	"""Return two lists of length n containing elements over the ring.
	It holds that for both lists the product of all a_i looking at the 
	same index are the same
	"""
	
	assert(n>0)
	alphas = _randomElements(ring, n)
	alphasP = _randomElements(ring, n)
	
	for i in range(max(indexList)+1):
		alphasForIndex = [alpha for alpha, index in zip(alphas, indexList) if index == i]
		targetValue = reduce(mul, alphasForIndex, ring(1))
		
		alphasPForIndex = [alpha for alpha, index in zip(alphasP, indexList) if index == i]
		primeValue = reduce(mul, alphasPForIndex, ring(1))
		
		#change the first value of the first alphaP belonging to the current index so that the products will be identical
		try:
			firstIndex = indexList.index(i)
			alphasP[firstIndex] = (targetValue*alphasP[firstIndex]) / primeValue
		except ValueError:
			pass
	
	return (alphas, alphasP)

def _generateVectors(ring):
	"""Generate four 5-element lists s*, t*, s'*, t'*, so that <s*, t*> == <s'*, t'*>"""
	
	sS = _randomElements(ring, 5)
	tS = _randomElements(ring, 5)
	targetValue = sum([a*b for a, b in zip(sS, tS)])
	
	sPS = _randomElements(ring, 5)
	tPS = _randomElements(ring, 5)
	primeValue = sum([a*b for a, b in zip(sPS, tPS)])
	
	#change first value of sPS so that the dot products will match
	sPS[0] = (targetValue - primeValue + sPS[0]*tPS[0]) / tPS[0]

	return (sS, tS, sPS, tPS)

def _randomElements(ring, n):
	"""Return a list of length n with random elements (except 0) from ring"""
	
	assert(n>=0)
	ret = []
	
	while(len(ret)<n):
		new = ring.random_element()
		if new != ring(0): ret.append(new)
	
	return ret

if __name__ == '__main__':
	
	from itertools import product
	from circuit import *
	
	inputLength = 4
	inputs = [Input('x') for _ in range(0, inputLength)]
	
	# -(x0&x1)&(-x2&x3)
	crc = Circuit(AndGate(NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[2]), inputs[3])))
	print 'Circuit: %s'%(crc)
	
	bp = BranchingProgram.fromCircuit(crc)
	print bp
	
	rbp = RandomizedBranchingProgram.fromCircuit(crc, 1049)
	print rbp
	
	for test in list(product([0,1], repeat=inputLength)):
		test = list(test)
		bpResult = bp.evaluate(test)
		rbpResult = rbp.evaluate(test)
		print('Input: %s => BP: %d, RBP: %d, equal?: %s'%(test, bpResult, rbpResult, bpResult==rbpResult))