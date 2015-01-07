"""Determine execution times for the different intermediate steps of
the indistinguishability obfuscation candidate.

Experiment IDs:

0: Universal Circuit evaluation
1: Branching Program evaluation
2: Randomized Branching Program evaluation
3: Fixed Randomized Branching Program evaluation
4: Bigger RBP (generation experiment #4) evaluation
"""

from sage.all import *
import sys, os
import logging
import cPickle
import sqlite3
from itertools import product

from obfusc8.circuit import *
from obfusc8.blocks import UniversalCircuit
from obfusc8.experiments.timer import Timer
from obfusc8.experiments.shared_parameters import *

def experiment(pList, fileFormatString, experimentName):
	"""Load the correct objects and calls the evaluate() function on
	them. 
	
	Measure execution time and check for correctness of the
	evaluation. Additionally handle logging setup and writing all results
	into the database.

	pList is the list of parameter tuples on which the expFunction
		will be executed. One tuple corresponds to one step of the 
		experiment.
	fileFormatString describes how to name the output files dependent on
		the parameter of the experiment step.
	experimentName is the name of the output folder and doubles as name
		of the table in which the results are stored.
	
	This function will catch all exceptions besides KeyboardInterrupt,
	if the global blockExceptions is set to True.
	"""
	
	for params in pList:
		#--- setup ---
		filename = fileFormatString.format(*params)
		
		localHandler = logging.FileHandler('results/execution/%s.log'%filename)
		rootLogger = logging.getLogger()
		rootLogger.addHandler(localHandler)
		
		try:
			inputLength = params[0]
			numberOfGates = params[1]
			
			circuits = cLists['%d%d'%(inputLength, numberOfGates)]
			
			logging.warning('Loading %s'%filename)
			with open('results/%s/%s.pkl'%(experimentName, filename), 'rb') as input:
				evaluator = cPickle.load(input)
			logging.warning('%s'%evaluator)
			
			circuitTimes = []
			results = []
			correct = []
			
			for crc in circuits:
				ctrlInput = UniversalCircuit.obtainCtrlInput(crc) if experimentName is not 'rbpsFix' else []
				for test in list(product([0,1], repeat=inputLength)):
					inp = list(test)
					with Timer() as t:
						expectedResult = crc.evaluate(inp)
					circuitTimes.append(t.secs)
					with Timer() as t:
						result = evaluator.evaluate(ctrlInput+inp)
					results.append(t.secs)
					correct.append(result==expectedResult)
					logging.info('%s => %d in %f seconds (this is %s)'%(inp, result, t.secs, result==expectedResult))
			
			averageCircuit = sum(circuitTimes)/len(circuitTimes)
			logging.info('Average circuit evaluation time: %f'%averageCircuit)
			
			average = sum(results)/len(results)
			logging.info('Average evaluation time: %f'%average)

			logging.info('Correct result %d times'%correct.count(True))
			logging.info('Wrong result %d times'%correct.count(False))
			
			#log into database
			logging.warn('Writing to database')
			c = resultsDB.cursor()
			
			dbInput = (filename, averageCircuit, average, correct.count(True), correct.count(False))
			placeholders = ','.join(['?']*len(dbInput))
			c.execute('INSERT INTO %sEval Values (%s)'%(experimentName, placeholders), dbInput)
			
			resultsDB.commit()
			
		except KeyboardInterrupt:
			logging.error('User abort!')
			break
		except:
			logging.error('Caught exception!')
			logging.error(sys.exc_info()[0])
			if not blockExceptions:
				raise
				
		rootLogger.removeHandler(localHandler)
		
def make_sure_path_exists(path):
	"""Create all directories in path if they do not exist."""
	
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
			
if __name__ == '__main__':
	
	blockExceptions = True
	
	#---------------- Setup ------------------
	
	#ensure folder existence
	make_sure_path_exists('results/execution')
	
	#database
	resultsDB = sqlite3.connect('results.db')
	
	#logging config
	fileHandler = logging.FileHandler('execution.log')
	fileHandler.setLevel(logging.DEBUG)
	logging.getLogger().addHandler(fileHandler)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setLevel(logging.WARNING)
	logging.getLogger().addHandler(consoleHandler)
	
	#paramter 'parsing'
	if len(sys.argv) == 1:
		logging.warn('Running all tests specified')
		testList = range(4)
	else:
		testList = [int(i) for i in sys.argv[1].split(',')]
		logging.warn('Running only tests No. %s'%testList)
	
	if 0 in testList:
		#---------------- UC Tests ------------------
		logging.warn('-------- UC tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS ucsEval (name text, averageCircuit real, average real, correct integer, incorrect integer)''')
		resultsDB.commit()
		
		experiment(smallUCList, 'uc_{0}_{1}', 'ucs')
	
	if 1 in testList:
		#---------------- BP Tests ------------------
		logging.warn('-------- BP tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS bpsEval (name text, averageCircuit real, average real, correct integer, incorrect integer)''')
		resultsDB.commit()
		
		experiment(smallUCList, 'bp_{0}_{1}', 'bps')
		
	if 2 in testList:
		#---------------- Simple RBP Tests ------------------
		logging.warn('-------- Simple RBP tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS rbpsEval (name text, averageCircuit real, average real, correct integer, incorrect integer)''')
		resultsDB.commit()
		
		experiment(ukDimPList, 'rbp_{0}_{1}_{2}_{3}', 'rbps')
		
	if 3 in testList:
		#---------------- Fix BP Tests ------------------
		logging.warn('-------- Fix BP Tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS bpsFixEval (name text, averageCircuit real, average real, correct integer, incorrect integer)''')
		resultsDB.commit()
		
		experiment(smallUCList, 'bpFix_{0}_{1}', 'bpsFix')
		
	if 4 in testList:
		#---------------- Bigger RBP Tests ------------------
		logging.warn('-------- Bigger RBP Tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS rbpMatSizeEval (name text, averageCircuit real, average real, correct integer, incorrect integer)''')
		resultsDB.commit()
		
		experiment(ukDimPList, 'rbp_{0}_{1}_{2}_{3}', 'rbpMatSize')
		
	resultsDB.close()