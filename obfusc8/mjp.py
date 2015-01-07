"""Attempt to implement the Multilinear Jigsaw Puzzles as described 
in Appendix A of the paper [0].

!!! ATTENTION !!! 
There are several issues and this implementation is NOT working 
correctly for now. 
!!! ATTENTION !!! 

0. Parameter Choices:
	Generally the correct choice of parameters and the relation between
	them seems to be a bit underspecified. While there is a 'Setting
	Parameters' paragraph in Appendix A, it relies heavily on Big O
	notation and was a bit confusing to us in other regards (e.g.
	why is m an effective security parameter, even though there already
	exists the dedicated security parameter lambda?)

1. a mod g:
	The first step of encoding an element a is to calculate 
	"a_hat = a modulo (g) to create a small polynomial". We could
	not think of a better canonical representative for this reduction 
	than a itself, which makes us believe that either the modulo reduction
	is redundant or the authors had another canonical representative in 
	mind (a polynomial) which is unclear how to compute.

2. Size of m:
	In the already mentioned 'Setting Parameters' paragraph, it is said that
	k = m^delta even though k is actually an input parameter. If we infer
	from this that m = k^(1/delta) we run into massive performance problems
	for even the tiniest RBPs. We tried to use constant values for m (see
	_getM) until we realized that this will completely change the value of
	q, q^(7/8), p etc. 
	
3. Application of mod p:
	It remains unclear how the (mod p) which is inherent to the computations
	over Z_p that 'plaintext' RBPs perform is applied in the encoding.
	Currently computations in the encoding work as expected unless the
	results grow larger than p.
	
	This is most probably related to (0), (1) and (2).

4. Error Terms:
	When encoding an element a, the second step is to choose an error 
	term e, so that a_hat + e*g is 'discrete Gaussian centered at the 
	origin'. We are not entirely sure how to ensure this. Currently we
	only choose small random coefficients for the error terms.

[0] S. Garg, C. Gentry, S. Halevi, M. Raykova, A. Sahai, and B. Waters. "Candidate
indistinguishability obfuscation and functional encryption for all circuits." In:
Foundations of Computer Science (FOCS), 2013 IEEE 54th Annual Symposium on.
IEEE. 2013, pp. 40-49.
"""

from sage.all import *
from operator import mul
import logging

class JigsawPuzzle(object):
	"""Multilinear Jigsaw Puzzles as defined in Appendix A"""

	def __init__(self, k, secParam, dimensionality=None, delta=0.5, epsilon=0.55):
		logging.info("--- Starting Jigsaw Puzzle generation ----")
		
		self.x = SR.var('x')
		
		#--- constants ---
		#0 < delta < epsilon < 1
		#delta down -> m up, g depends on m and delta
		self.delta = delta
		#epsilon down -> q down
		self.epsilon = epsilon
		self.k = k
		self.secParam = secParam
		
		#Dimensionality m	
		self.m = self.__getM(dimensionality)
		logging.debug('m: %d'%self.m)
		
		#choose 'large' random prime q
		#q should be aproximately 2^O(m^epsilon)
		q_exp = int((self.__getM(dimensionality)**self.epsilon))*10
		self.q = random_prime (2**(q_exp+1), lbound=2**q_exp)
		logging.debug('%d < q < %d ==> q: %d'%(2**q_exp, 2**(q_exp+1), self.q))
		
		#generate ring R = Z[X]/(X^m+1) and R_q = Z_q[X]/(X^m+1) (m = dimension parameter)
		self.R = QuotientRing(ZZ[self.x], self.x**self.m+1)
		self.t = self.R.gen()
		self.R_q = QuotientRing(Integers(self.q)[self.x], self.x**self.m+1)
		
		#choose small random polynomial g element R, |R/g)| is a large prime p, + more conditions
		self.g = self.__chooseG()
		logging.debug('g_bound: %d => g: %s' % (2**int(self.m**self.delta), self.g))
		logging.debug('p: %d'%self.getP())
		
		#choose k random polynomials z_1, z_2, ..., z_k
		self.zList = self.__getZList()
		
		#generate zero test element
		self.pzt = self.__getPzt()
		logging.debug('Zero test element: %s' % self.pzt)

		logging.info("--- Jigsaw Puzzle generation successful ---")
	
	def encode(self, a, levelSet):
		"""Encode the element a at the level described by levelSet"""
		
		assert(all(i<self.k for i in levelSet))
		
		#reduce a modulo (g) to get small polynomial a^ in R
		aHat = self.R(a).mod(self.g)

		#choose error so that it is small and a^+e*g is discrete centered at the origin
		#all coefficients smaller than 2^O(m^delta)
		bound = 2**(int(self.m**self.delta)/2)
		coeffs = [ZZ.random_element(0, bound) for i in range(self.m)]
		error = sum([a*self.t**i for a, i in zip(coeffs, range(len(coeffs)))])
		
		#return: (a^ + e*g) / product of all z_i (i elem S)
		numerator = self.R_q(aHat + error*self.g)
		denominator = self.R_q(reduce(mul, [self.zList[i] for i in levelSet]))
		
		return numerator/denominator
		
	def encodeMatrix(self, mat, levelSet):
		"""Encode all elements of matrix at the level levelSet"""
		
		enc = self.encode
		return mat.apply_map(lambda z: enc(z, levelSet))
	
	def isZero(self, u):
		"""Test if u is a valid encoding of 0 at the highest level"""
		
		logging.info('Starting zero test.')
		
		#should only be h*e
		v = self.R_q(u*self.pzt)
		
		#test if v is small enough -> has canonical embedding of Euclidean Norm smaller than q^(7/8)
		norm = float(sum([int(a)**2 for a in v.list()]))**(0.5)
		
		ret = norm < (self.q**(7/8.0))
		logging.info('Zero test result: %f < %f => %s'%(norm, self.q**(7/8.0), ret))
		return ret
		
	def getP(self):
		"""Return the prime p that identifies the plaintext space of the input."""
		
		return self.p
		
	def elementNorm(self, u):
		"""Debug Helper: Calculate the norm of one element"""
		
		v = self.R_q(u*self.pzt)
		norm = float(sum([int(a)**2 for a in v.list()]))**(0.5)
		return norm
		
	def __getZList(self):
		"""Return self.k random polynomials over self.R_q which are all invertible"""
		
		ret = []
		while not(len(ret)==self.k):
			new = self.R_q.random_element()
			try:
				tmp = 1/new
				ret.append(new)
			except:
				pass
		return ret

	def __chooseG(self):
		"""Choose a 'small' polynomial g subject to several conditions
		
		Conditions:
		- each coefficient should be smaller than 2^O(m^delta)
		- |R/(g)| is a large prime p (p > 2^lambda)
		- g^-1 when viewed in Q[X]/(X^m+1) is sufficiently small
		"""
		
		qr = QuotientRing(QQ[self.x], self.x**self.m+1)
		cond = False
		bound = 2**(int(self.m**self.delta))
		
		while not(cond):
			#all coefficients smaller than 2^O(m^delta)
			coeffs = [ZZ.random_element(0, bound) for i in range(self.m)]
			g = sum([a*self.t**i for a, i in zip(coeffs, range(len(coeffs)))])

			#conditions:
			#|R/(g)| is large prime p (p > 2^lambda/securityParameter)
			self.p = g.norm()
			p = self.p
			cond = p > 2**self.secParam and p in Primes()

			#g^-1 when viewed in Q[X]/(X^m+1) sufficiently small
			if cond:
				g_1 = qr(g)**(-1)
				cond = all([abs(c) < bound for c in g_1.list()])
		
		return g
		
	def __getPzt(self):
		"""Generate the zero test parameter"""
		
		#random 'mid-size' polynimial, chosen from a discrete Gaussian in R, coefficients are of size roughly q^(2/3)
		coeffs = [ZZ.random_element(int(0.9*self.q**(2/3.0)), int(1.1*self.q**(2/3.0))) for i in range(self.m)]
		h = sum([a*self.t**i for a, i in zip(coeffs, range(len(coeffs)))])
		#pzt = h*product of all z_i / g
		return h*reduce(mul, self.zList)/self.g
	
	def __getM(self, dim):
		"""Chooses m according to dim.
		
		m = None -> use the standard way described in the paper.
		otherwise use dim directly as long as it is > 0 and a power of two
		"""
		ret = -1
		if dim is None:
			#k should be = m^delta -> m = k^(1/delta)
			ret = self.k**(1/self.delta)
			#needs be power of two
			ret = 2**int(math.log(ret, 2))
		else:
			assert(dim > 0)
			#is power of two?
			assert((dim & (dim - 1)) == 0)
			#use constant for reasonable runtimes
			ret = dim
		assert(ret != -1)
		return ret
		
	def __str__(self):
		return 'Multilinear Jigsaw Puzzle with k: %d, P: %d, q: %d' % (self.k, self.getP(), self.q)
	
if __name__ == '__main__':
	length = 5
	puzzle = JigsawPuzzle(length+2, 2, dimensionality=2**3, delta=0.4, epsilon=0.5)
	ring = Integers(puzzle.getP())
	
	print puzzle
	print 'q^(7/8): %f' % (puzzle.q**(7/8.0))
	
	zeroEnc = puzzle.encode(ring(0), range(length+2))
	
	print 'encryption of zero: %s'%zeroEnc

	print 'is zero? %s'%puzzle.isZero(zeroEnc)