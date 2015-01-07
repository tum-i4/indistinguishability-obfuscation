"""Generate the mappings used in the fast Branching Program generation.

This module contains the code that was used to generate the mappings that
are used to generate Branching Programs by applying Barrington's Theorem.
Additionally it contains two earlier versions of the Branching Program
generation for explanatory purposes.

!!! 
Note that the earlier versions of Branching Program generation do not
work with the main code anymore, as the BP representation has changed.
Nonetheless they are useful for understanding what the new mapping code
is doing internally.
!!!
"""

from numpy import array, dot, where

#------------- helpers ---------------------

def _identity(): return array([[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1]])	#e			
def _normal(): return array([[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0],[0,0,0,0,1],[1,0,0,0,0]]) 		#(01234)
def _normalInv(): return array([[0,0,0,0,1],[1,0,0,0,0],[0,1,0,0,0],[0,0,1,0,0],[0,0,0,1,0]]) 	#(04321)
def _ni2n(): return array([[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0]])		#(14)(23)
def _n2sec(): return array([[1,0,0,0,0],[0,0,1,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,1,0,0,0]]) 		#(124)
def _n2secInv(): return array([[1,0,0,0,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,0,1,0],[0,0,1,0,0]])	#(142)
def _sec2si(): return array([[1,0,0,0,0],[0,0,1,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,0,1,0]]) 		#(12)(34)
#def _res2n(): return array([[1,0,0,0,0],[0,0,0,0,1],[0,0,0,1,0],[0,0,1,0,0],[0,1,0,0,0]]) 		#(14)(23)
def _special1(): return array([[1,0,0,0,0],[0,0,0,1,0],[0,0,0,0,1],[0,1,0,0,0],[0,0,1,0,0]]) 	#(13)(24)
def _special2(): return array([[1,0,0,0,0],[0,1,0,0,0],[0,0,0,0,1],[0,0,1,0,0],[0,0,0,1,0]]) 	#(243)
def _special3(): return array([[1,0,0,0,0],[0,1,0,0,0],[0,0,0,1,0],[0,0,0,0,1],[0,0,1,0,0]]) 	#(234)

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
	
#------------- First version ---------------------
# This version is essentially a recursive implementation of the inductive
# proof of Barrington's theorem as presented in [0]. In order to facilitate
# the recursion, the resulting BPs are 'normalized' after each step, that is
# they will evaluate to A_0 = e if the corresponding circuit evaluates to 0
# and to A_1 = (01234)  if the corresponding circuit evaluates to 1.
# Additional information on this can also be found in [1].
#
#[0] K. Hansen and C. Jensen. Barrington’s Theorem. url: http://www.cs.au.dk/~arnsfelt/CT10/scribenotes/lecture16.pdf
#[1] N. Kunze. "A Qualitative Study of Indistinguishability Obfuscation." BA thesis. Technische Universität München, 2014.

def oldC2BP1(circuit):
	instructions, indexList = _getInstructions1(circuit.outputGate)
	#make sure one perm is the identity
	instructions.append((_normalInv(), _normalInv()))
	ins0 = [tpl[0] for tpl in instructions]
	ins1 = [tpl[1] for tpl in instructions]
	indexList.append(0)
	return BranchingProgram(ins0, ins1, indexList, _normalInv(), _identity())
	
def _getInstructions1(gate):
	#Input
	if gate.getType() == -1:
		ins = (_identity(), _normal())
		return ([ins], [gate.pos])
	
	#NotGate
	elif gate.getType() == 0:
		instructions, indexList = _getInstructions1(gate.input1)
		#apply o^-1 in the end
		instructions[-1] = tuple(dot(instructions[-1][i],_normalInv()) for i in range(2))
		#normalize program
		a = _ni2n()
		instructions = [_changeBoth(ins, a, a) for ins in instructions]
		return (instructions, indexList)
		
	#AndGate
	elif gate.getType() == 1:
		instructions1, indexList1 = _getInstructions1(gate.input1)
		instructions2, indexList2 = _getInstructions1(gate.input2)
		
		#assemble new program
		a1 = instructions1
		a2 = [_changeBoth(ins, _n2secInv(), _n2sec()) for ins in instructions2]
		a3 = [_changeBoth(ins, _ni2n(), _ni2n()) for ins in instructions1]
		a4 = [_changeBoth(ins, _sec2si(), _sec2si()) for ins in a2]
		
		#normalize new program
		newIns = a1 + a2 + a3 + a4
		newIns = [_changeBoth(ins, _sec2si(), _sec2si()) for ins in newIns]
		newIndexList = indexList1 + indexList2 + indexList1 + indexList2
		
		return (newIns, newIndexList)
		
	raise ValueError
	
#------------- Second version ---------------------
# The most notable change of this version in comparison to the first one
# is that transformation and normalization are now performed in one step
# in the AndGate branch. That is, instead of first applying the permutations
# necessary to generate a_i (i in [1, 4) and then normalizing the assembled
# program a1+a2+a3+a4 by applying _sec2si, each a_i is already normalized.

def oldC2BP2(circuit):
	instructions, indexList = _getInstructions2(circuit.outputGate)
	#make sure one perm is the identity
	instructions.append((_normalInv(), _normalInv()))
	ins0 = [tpl[0] for tpl in instructions]
	ins1 = [tpl[1] for tpl in instructions]
	indexList.append(0)
	return BranchingProgram(ins0, ins1, indexList, _normalInv(), _identity())
	
def _getInstructions2(gate):
	#Input
	if gate.getType() == -1:
		ins = (_identity(), _normal())
		return ([ins], [gate.pos])
	
	#NotGate
	elif gate.getType() == 0:
		instructions, indexList = _getInstructions2(gate.input1)
		#apply o^-1 in the end
		instructions[-1] = tuple(dot(instructions[-1][i],_normalInv()) for i in range(2))
		#normalize program
		a = _ni2n()
		instructions = [_changeBoth(ins, a, a) for ins in instructions]
		return (instructions, indexList)
	
	#AndGate
	elif gate.getType() == 1:
		instructions1, indexList1 = _getInstructions2(gate.input1)
		
		#transformation for new program + normalization applied at the same time
		a = _sec2si()
		a1 = [_changeBoth(ins, a, a) for ins in instructions1]
		a = _special1()
		a3 = [_changeBoth(ins, a, a) for ins in instructions1]
		instructions1 = None
		
		instructions2, indexList2 = _getInstructions2(gate.input2)
		
		a = _special2()
		b = _special3()
		a2 = [_changeBoth(ins, a, b) for ins in instructions2]
		a = _n2secInv()
		b = _n2sec()
		a4 = [_changeBoth(ins, a, b) for ins in instructions2]
		instructions2 = None
		
		return (a1+a2+a3+a4, indexList1+indexList2+indexList1+indexList2)
		
	raise ValueError

#------------- generate mappings ---------------------
# The basic principle behind the mappings is quite simple. So far
# even during generation the intermediate Branching Programs consist
# of permutation matrices. During the generation of BPs from Universal
# Circuits, this causes very high memory consumption, because of the
# way that the recursive calls are made. In order to lessen the impact
# of this, we assign each possible permutation in S_5 (there are only
# 120 in total) a unique integer ID.
#
# Since we still need to apply different permutations to the IDs, we
# then generate a mapping for each operation which describes the resulting
# permutation ID for each input ID.
#
# Since integers use much less memory than the 5x5 permutation matrices,
# using these IDs greatly alleviates the memory problem.

def getPossiblePerms():
	"""Generate a list with all possible permutations in S_5.

	This is done by consecutively applying the 6 different operations that
	occur during the Branching Program generation process to the permutations
	that were already found, until no new permutations form. The unique ID
	of each permutation is simply its position in said list.
	"""

	permList = [_matrix2cycle(_identity()), _matrix2cycle(_normal())]
	string2Perm = {_matrix2cycle(_identity()):_identity(), _matrix2cycle(_normal()):_normal()}
	lenOld = 0
	
	def addIfNew():
		newPermS = _matrix2cycle(newPerm)
		if not newPermS in permList:
			permList.append(newPermS)
			string2Perm[newPermS] = newPerm
	
	#repeat until we didn't find anything new
	while lenOld < len(permList):
		lenOld = len(permList)
		for permS in permList:
			perm = string2Perm[permS]
			
			#--- NotGate ---
			#only last
			newPerm = dot(dot(_ni2n(), dot(perm, _normalInv())), _ni2n())
			addIfNew()
			
			#all
			newPerm = dot(dot(_ni2n(), perm), _ni2n())
			addIfNew()
			
			#--- AndGate ---
			#a1
			newPerm = dot(dot(_sec2si(), perm), _sec2si())
			addIfNew()
			
			#a3
			newPerm = dot(dot(_special1(), perm), _special1())
			addIfNew()
			
			#a2
			newPerm = dot(dot(_special2(), perm), _special3())
			addIfNew()
			
			#a4
			newPerm = dot(dot(_n2secInv(), perm), _n2sec())
			addIfNew()
	
	return (permList, string2Perm)
	
def calculateMappings(permList, string2Perm):
	"""Take the output of getPossiblePerms() and compute the mappings
	for each of the 6 needed operations.
	"""

	mappings = [range(len(permList)) for _ in range(6)]
	
	for permInd, permS in zip(range(len(permList)), permList):
		perm = string2Perm[permS]

		#--- NotGate ---
		#only last
		newPerm = dot(dot(_ni2n(), dot(perm, _normalInv())), _ni2n())
		newPermS = _matrix2cycle(newPerm)
		newPermInd = permList.index(newPermS)
		mappings[0][permInd] = newPermInd
		
		#all
		newPerm = dot(dot(_ni2n(), perm), _ni2n())
		newPermS = _matrix2cycle(newPerm)
		newPermInd = permList.index(newPermS)
		mappings[1][permInd] = newPermInd
		
		#--- AndGate ---
		#a1
		newPerm = dot(dot(_sec2si(), perm), _sec2si())
		newPermS = _matrix2cycle(newPerm)
		newPermInd = permList.index(newPermS)
		mappings[2][permInd] = newPermInd
		
		#a3
		newPerm = dot(dot(_special1(), perm), _special1())
		newPermS = _matrix2cycle(newPerm)
		newPermInd = permList.index(newPermS)
		mappings[3][permInd] = newPermInd
		
		#a2
		newPerm = dot(dot(_special2(), perm), _special3())
		newPermS = _matrix2cycle(newPerm)
		newPermInd = permList.index(newPermS)
		mappings[4][permInd] = newPermInd
		
		#a4
		newPerm = dot(dot(_n2secInv(), perm), _n2sec())
		newPermS = _matrix2cycle(newPerm)
		newPermInd = permList.index(newPermS)
		mappings[5][permInd] = newPermInd
		
	return mappings

if __name__=='__main__':
	permList, string2Perm = getPossiblePerms()
	print 'Mappings:'
	print calculateMappings(permList, string2Perm)
	print 'id2permList:'
	print [string2Perm[s] for s in permList]
	