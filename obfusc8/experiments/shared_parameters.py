from obfusc8.circuit import *

#---------------- Parameters ------------------

#test on all useful pairs of numInputs / numGates for 
maxInputs = 4
#relationship: ins-1 <= gates <= 3*ins - 2
ukList =  [(inp, gates) for inp in range(2, maxInputs+1) for gates in range(inp-1, 3*inp-1)]

#ucs that can realistically be transformed into bps, sorted by number of andGates
smallUCList = [(2, 1), (2,2), (3,2), (2,3), (3,3), (4,3)]

#matrix dimensions for rbp generation
dimList = [1]
#small (4 digits), medium (6 digits), large (9 digits)
pList = [104395301]#,[1049, 100003]#, 104395301]
ukDimPList = [(u, k, dim, p) for p in pList for u, k in smallUCList for dim in dimList]

#one rbp with different dimensions
rbpDimList = [(2, 1, dim, 1015747) for dim in [2, 3, 4, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]]

#all possible circuits for particular #gates and #inputs
inputs = [Input('x') for _ in range(0, maxInputs)]
cl21 = [Circuit(AndGate(inputs[0], inputs[1]))]
cl22 = map(Circuit, [NotGate(AndGate(inputs[0], inputs[1])), AndGate(NotGate(inputs[0]), inputs[1]), AndGate(inputs[0], NotGate(inputs[1]))])
cl32 = [Circuit(AndGate(AndGate(inputs[0], inputs[1]), inputs[2]))]
cl23 = [Circuit(AndGate(NotGate(inputs[0]), NotGate(inputs[1])))]
cl33 = map(Circuit, [NotGate(AndGate(AndGate(inputs[0], inputs[1]), inputs[2])), AndGate(NotGate(AndGate(inputs[0], inputs[1])), 
	inputs[2]), AndGate(AndGate(inputs[0], inputs[1]), NotGate(inputs[2])), AndGate(AndGate(NotGate(inputs[0]), inputs[1]), inputs[2]), 
	AndGate(AndGate(inputs[0], NotGate(inputs[1])), inputs[2])])
cl43 =	[Circuit(AndGate(AndGate(AndGate(inputs[0], inputs[1]), inputs[2]), inputs[3]))]

cLists = {'21':cl21, '22':cl22, '32':cl32, '23':cl23, '33':cl33, '43':cl43}

#circuits for fixing
circuitList = [cl21[0], cl22[0], cl32[0], cl23[0], cl33[0], cl43[0]]
bpFixParams = [tpl+(crcs,) for tpl, crcs in zip(smallUCList, circuitList)]