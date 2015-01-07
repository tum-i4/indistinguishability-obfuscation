"""Trying to understand: how long does it take to a) setup the mjp,
b) encode one element and c) add/multiply two elements.
Also investigates memory needed for setup and the growth of the encode elements.
"""

import sqlite3
import logging
from guppy import hpy

from obfusc8.timer import Timer
from obfusc8.mjp import *

#database setup
resultsDB = sqlite3.connect('results.db')
c = resultsDB.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS mjpSetup (dimension integer, levels integer, memory integer, time real)''')
c.execute('''CREATE TABLE IF NOT EXISTS mjpEncode (dimension integer, levels integer, memoryBefore integer, memoryAfter integer, increase real, time real)''')
c.execute('''CREATE TABLE IF NOT EXISTS mjpAdd (dimension integer, levels integer, timePlain real, timeEnc real, increase real)''')
c.execute('''CREATE TABLE IF NOT EXISTS mjpMultiply (dimension integer, levels integer, timePlain real, timeEnc real, increase real)''')
resultsDB.commit()

#logging setup
fileHandler = logging.FileHandler('mjp.log')
fileHandler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.WARNING)
logging.getLogger().addHandler(consoleHandler)

#parameters
dimList = [32, 64]
levels = [10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

paramList = [(dim, lvl) for dim in dimList for lvl in levels]

repetitions = 100

hp = hpy()

for dim, lvl in paramList:
	#------------------------------------------------------------
	#a) mjp 
	logging.warning('MJP Setup with m = %d and %d levels'%(dim, lvl))
	hp.setrelheap()
	with Timer() as t:
		mjp = JigsawPuzzle(lvl, 2, dimensionality=dim)
	memoryUsage = hp.heap().size
	
	logging.info('Memory usage: %d'%memoryUsage)
	logging.info('Time elapsed: %f'%t.secs)
	
	c.execute('INSERT INTO mjpSetup Values (?,?,?,?)', (dim, lvl, memoryUsage, t.secs))
	resultsDB.commit()
	
	for _ in range(10):
		#------------------------------------------------------------
		#b) encode one element (at highest level = slowest)
		logging.warning('Encoding start')
		
		ring = Integers(mjp.getP())
		
		hp.setrelheap()
		add1 = ring.random_element()
		add2 = ring.random_element()
		mult1 = ring.random_element()
		mult2 = ring.random_element()
		before = hp.heap().size / 4
		
		hp.setrelheap()
		with Timer() as t:
			add1Enc = mjp.encode(add1, range(lvl))
			add2Enc = mjp.encode(add2, range(lvl))
			mult1Enc = mjp.encode(mult1, range(lvl/2))
			mult2Enc = mjp.encode(mult2, range(lvl/2, lvl))
		execTime = t.secs / 4
		after = hp.heap().size / 4
		
		increase = after/(before*1.0)
		
		logging.info('Memory usage before: %d'%before)
		logging.info('Memory usage after: %d'%after)
		logging.info('Increase: %f'%increase)
		logging.info('Time elapsed each: %f'%execTime)
		
		c.execute('INSERT INTO mjpEncode Values (?,?,?,?,?,?)', (dim, lvl, before, after, increase, execTime))
		resultsDB.commit()

		#------------------------------------------------------------
		#c) add/multiply two elements (add: highest, multiply: to highest?)
		logging.warning('Evaluation start')
		
		#add
		with Timer() as t:
			for _ in range(repetitions): resAdd = add1 + add2
		timePlainAdd = t.secs / repetitions
		with Timer() as t:
			for _ in range(repetitions): resAddEnc = add1Enc + add2Enc
		timeEncAdd = t.secs / repetitions
		increaseAdd = timeEncAdd/(timePlainAdd*1.0)
		logging.info('add plain %f, enc %f => increase %f'%(timePlainAdd, timeEncAdd, increaseAdd))
		c.execute('INSERT INTO mjpAdd Values (?,?,?,?,?)', (dim, lvl, timePlainAdd, timeEncAdd, increaseAdd))
		resultsDB.commit()
		
		#multiply
		with Timer() as t:
			for _ in range(repetitions): resMult = mult1 + mult2
		timePlainMult = t.secs / repetitions
		with Timer() as t:
			for _ in range(repetitions): resMultEnc = mult1Enc + mult2Enc
		timeEncMult = t.secs / repetitions
		increaseMult = timeEncMult/(timePlainMult*1.0)
		logging.info('mult plain %f, enc %f => increase %f'%(timePlainMult, timeEncMult, increaseMult))
		c.execute('INSERT INTO mjpMultiply Values (?,?,?,?,?)', (dim, lvl, timePlainMult, timeEncMult, increaseMult))
		resultsDB.commit()
	
resultsDB.close()