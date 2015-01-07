"""Generate the different steps of the indistinguishability obfuscation 
candidate and measure memory and time impact.

Experiment IDs:

0: generate all useful UCs up to a input size of 4
1: Generate BPs for 'small' UCs [(2, 1), (2,2), (3,2), (2,3), (3,3), (4,3)]
2: Generate RBPs for 'small' UCs with three different primes
3: fix BPs for 'small' UCs with one arbitrary circuit
4: generate one RBP with different matrix dimensions than 1 ([1, 2, 3, 4, 5, 10, 100])

Dependencies: (a -> b means a needs to be run before b)

0 -> 1 -> 2
1 -> 3
1 -> 4
"""

import sys, os, errno
import logging
from guppy import hpy
import cPickle
import sqlite3

from obfusc8.obf import *
from obfusc8.bp import BranchingProgram
from obfusc8.experiments.timer import Timer
from obfusc8.experiments.shared_parameters import *

def experiment(expFunction, pList, fileFormatString, experimentName, inputFilesFormatString):
	"""Take care of all tasks that are identical for each experiment.
	This includes logging setup, saving intermediate objects, measuring
	some additional data and writing all results into the database.
	
	expFunction is the function that shall be executed during one
		step of the experiment.
	pList is the list of parameter tuples on which the expFunction
		will be executed. One tuple corresponds to one step of the 
		experiment.
	fileFormatString describes how to name the output files dependent on
		the parameter of the experiment step.
	experimentName is the name of the output folder and doubles as name
		of the table in which the results are stored.
	inputFilesFormatString describes where the files of a preceding step
		can be found, if so needed.
	
	This function will catch all exceptions besides KeyboardInterrupt,
	if the global blockExceptions is set to True.
	"""
	
	for params in pList:
		#--- setup ---
		filename = fileFormatString.format(*params)
		path = 'results/%s/%s'%(experimentName,filename)
		
		localHandler = logging.FileHandler(path+'.log')
		rootLogger = logging.getLogger()
		rootLogger.addHandler(localHandler)
		
		try:
			obj, dbInfo, execTime = expFunction(params, inputFilesFormatString)
			
			#Saving
			logging.warn('Saving object to %s.pkl'%path)
			with open(path+'.pkl', 'wb') as output:
				cPickle.dump(obj, output, -1)
			
			#log into database
			logging.warn('Writing to database')
			c = resultsDB.cursor()
			
			filesize = os.path.getsize(path+'.pkl')
			logging.info('Filesize: %d'%filesize)
			logging.info('Generation Time: %f'%execTime)
			
			dbInput = (filename,) + dbInfo + (filesize, execTime)
			placeholders = ','.join(['?']*len(dbInput))
			c.execute('INSERT INTO %s Values (%s)'%(experimentName, placeholders), dbInput)
			
			resultsDB.commit()
			
		except KeyboardInterrupt:
			logging.error('User abort!')
			break
		except:
			logging.error('Caught exception!')
			logging.error(sys.exc_info()[0])
			if not blockExceptions:
				raise
		finally:
			#'garbage collection'
			obj = None
			dbInfo = None
				
		rootLogger.removeHandler(localHandler)
	
def uc_exp(params, inputFilesFormatString):
	"""Universal circuit creation.
	
	params should be a tuple containing (inputLength, numberOfGates)
	"""

	inputLength, numberOfGates = params
	logging.warning('Starting UC generation for %d inputs and %d gates' % params)
	ioGen = IndistinguishabilityObfuscationGenerator(inputLength, numberOfGates, 100)
	
	hp.setrelheap()
	with Timer() as t:
		ioGen.generateUC()
	execTime = t.secs
	memoryUsage = hp.heap().size
	
	#Determine datapoints
	numAndGates = ioGen.uc.countGates(1)
	numAndGatesNoReuse = ioGen.uc.countGates(1, False)
	logging.info('Number of And Gates: %d (no reuse: %d)'%(numAndGates, numAndGatesNoReuse))
	
	numNotGates = ioGen.uc.countGates(0)
	numNotGatesNoReuse = ioGen.uc.countGates(0, False)
	logging.info('Number of Not Gates: %d (no reuse: %d)'%(numNotGates, numNotGatesNoReuse))
	logging.info('Number of Gates: %d'%(numAndGates+numNotGates))
	
	depth = ioGen.uc.getDepth()
	logging.info('Circuit depth: %d'%depth)
	
	estBPsize = BranchingProgram.estimateBPSize(ioGen.uc)
	logging.info('Estimated bp size: %d'%estBPsize)
	
	logging.info('Memory usage: %d'%memoryUsage)
	
	if estBPsize > 2**63: 
		estBPsize = -1
		logging.info('estimated size too big for sqlite integers')
	
	dbInfo = (inputLength, numberOfGates, numAndGates+numNotGates, numAndGates, numNotGates, numAndGatesNoReuse, numNotGatesNoReuse, depth, estBPsize, memoryUsage)	
	return (ioGen.uc, dbInfo, execTime)
	
def bp_exp(params, inputFilesFormatString):
	"""Transforming UCs into BPs.
	
	params should be a tuple containing (inputLength, numberOfGates)
	"""

	inputLength, numberOfGates = params
	logging.warning('Starting BP generation for %d inputs and %d gates' % params)
	ioGen = IndistinguishabilityObfuscationGenerator(inputLength, numberOfGates, 100)
	
	logging.info('Loading uc_%d_%d'%params)
	with open('results/'+inputFilesFormatString%params, 'rb') as input:
		ioGen.uc = cPickle.load(input)
	logging.warning('Loading successful: %s'%ioGen.uc)
	logging.warning('Estimated BP size: %d'%BranchingProgram.estimateBPSize(ioGen.uc))
	
	hp.setrelheap()
	with Timer() as t:
		ioGen.generateBP()
	execTime = t.secs
	memoryUsage = hp.heap().size
	bpSize = ioGen.bp.length
	
	logging.info('Memory usage: %d'%memoryUsage)
	logging.info('BP length: %d'%bpSize)
	
	dbInfo = (inputLength, numberOfGates, bpSize, memoryUsage)
	return (ioGen.bp, dbInfo, execTime)

def rbpSimple_exp(params, inputFilesFormatString):
	"""Transforming BPs into RBPs.
	
	params should be a tuple containing (inputLength, numberOfGates, matDimensions, p)
	"""

	inputLength, numberOfGates, matDimensions, p = params
	logging.warning('Starting RBP generation for %d inputs, %d gates with matDimensions %d and over Z modulo %d' % params)
	ioGen = IndistinguishabilityObfuscationGenerator(inputLength, numberOfGates, 100)
	
	if matDimensions==-1: matDimensions=None
	
	logging.info('Loading bp_%d_%d'%(inputLength, numberOfGates))
	with open('results/'+inputFilesFormatString%(inputLength, numberOfGates), 'rb') as input:
		ioGen.bp = cPickle.load(input)
	logging.warning('Loading successful: %s'%ioGen.bp)
	
	hp.setrelheap()
	with Timer() as t:
		ioGen.generateRBPSpecial(matDimensions, p)
	execTime = t.secs
	memoryUsage = hp.heap().size
	rbpLength = ioGen.rbp.length
	
	logging.info('RBP length: %d'%(rbpLength))
	logging.info('Memory usage: %d'%memoryUsage)
	
	dbInfo = (inputLength, numberOfGates, ioGen.rbp.m, p, rbpLength, memoryUsage)
	return (ioGen.rbp, dbInfo, execTime)

def bpFix_exp(params, inputFilesFormatString):
	"""Fix BP for a particular circuit.
	
	params should be a tuple containing (inputLength, numberOfGates, crc)
	"""

	inputLength, numberOfGates, crc = params
	logging.warning('Fixing BP for %d inputs and %d gates with circuit %s' % params)
	ioGen = IndistinguishabilityObfuscationGenerator(inputLength, numberOfGates, 100)
	
	logging.info('Loading bp_%d_%d'%(inputLength, numberOfGates))
	with open('results/'+inputFilesFormatString%(inputLength, numberOfGates), 'rb') as input:
		ioGen.bp = cPickle.load(input)
	logging.warning('Loading successful: %s'%ioGen.bp)
	
	hp.setrelheap()
	with Timer() as t:
		ioGen.bp = fixBP(ioGen.bp, crc)
	execTime = t.secs
	memoryUsage = hp.heap().size
	bpSize = ioGen.bp.length
	
	logging.info('Memory usage: %d'%memoryUsage)
	logging.info('Fixed BP length: %d'%bpSize)
	
	dbInfo = (inputLength, numberOfGates, bpSize, memoryUsage)
	return (ioGen.bp, dbInfo, execTime)

def make_sure_path_exists(path):
	"""Create all directories in path if they do not exist."""

    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

if __name__ == '__main__':
	
	blockExceptions = False;
	
	#---------------- Setup -----------------
	
	#ensure folder existence
	folders = ['ucs', 'bps', 'rbps', 'bpsFix', 'rbpMatSize']
	for dir in folders:
		make_sure_path_exists('results/%s'%dir)
	
	#database
	resultsDB = sqlite3.connect('results.db')
	
	#memory profiling
	hp = hpy()
	
	#logging config
	fileHandler = logging.FileHandler('generation.log')
	fileHandler.setLevel(logging.DEBUG)
	logging.getLogger().addHandler(fileHandler)
	
	#logging.basicConfig(format='%(levelname)s:%(message)s', filename='generation.log', level=logging.DEBUG)
	
	consoleHandler = logging.StreamHandler()
	consoleHandler.setLevel(logging.WARNING)
	logging.getLogger().addHandler(consoleHandler)
	
	#paramter 'parsing'
	if len(sys.argv) == 1:
		logging.warn('Running all tests specified')
		testList = range(6)
	else:
		testList = [int(i) for i in sys.argv[1].split(',')]
		logging.warn('Running only tests No. %s'%testList)
	
	if 0 in testList:
		#---------------- UC Tests ------------------
		logging.warn('-------- UC tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS ucs (name text, numInputs 
			integer, numSimGates integer, numGates integer, numAndGates 
			integer, numNotGates integer, numAndGatesNoReuse integer, 
			numNotGateNoReuse integer, depth integer, estBPsize integer, 
			memoryUsage integer, fileSize integer, genTime real)''')
		resultsDB.commit()
		
		experiment(uc_exp, ukList, 'uc_{0}_{1}', 'ucs', None)
	
	if 1 in testList:
		#---------------- BP Tests ------------------
		logging.warn('-------- BP tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS bps (name text, numInputs integer, 
			numSimGates integer, length integer, memoryUsage integer, fileSize integer, genTime real)''')
		resultsDB.commit()
		
		experiment(bp_exp, smallUCList, 'bp_{0}_{1}', 'bps', 'ucs/uc_%d_%d.pkl')
		
	if 2 in testList:
		#---------------- Simple RBP Tests ------------------
		logging.warn('-------- Simple RBP tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS rbps (name text, numInputs integer, 
			numSimGates integer, matrixDimensions integer, p integer, length integer, memoryUsage integer, fileSize integer, genTime real)''')
		resultsDB.commit()
		
		experiment(rbpSimple_exp, ukDimPList, 'rbp_{0}_{1}_{2}_{3}', 'rbps', 'bps/bp_%d_%d.pkl')

	if 3 in testList:
		#---------------- Fix BP Tests ------------------
		logging.warn('-------- Fix BP Tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS bpsFix (name text, numInputs integer, 
			numSimGates integer, length integer, memoryUsage integer, fileSize integer, genTime real)''')
		resultsDB.commit()
		
		experiment(bpFix_exp, bpFixParams, 'bpFix_{0}_{1}', 'bpsFix', 'bps/bp_%d_%d.pkl')
	
	if 4 in testList:
		#---------------- RBP matrix sizes Tests ------------------
		logging.warn('-------- RBP matrix sizes Tests --------')
		
		#prepare database
		c = resultsDB.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS rbpMatSize (name text, numInputs integer, 
			numSimGates integer, matrixDimensions integer, p integer, length integer, memoryUsage integer, fileSize integer, genTime real)''')
		resultsDB.commit()
		
		experiment(rbpSimple_exp, rbpDimList, 'rbp_{0}_{1}_{2}_{3}', 'rbpMatSize', 'bps/bp_%d_%d.pkl')
	
	#breakdown	
	resultsDB.close()