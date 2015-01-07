import unittest

testmodules = [
	'obfusc8.test.test_blocks', 
	'obfusc8.test.test_bp', 
	'obfusc8.test.test_circuit', 
	'obfusc8.test.test_mjp', 
	'obfusc8.test.test_obf', 
	'obfusc8.test.test_rbp'
	]

suite = unittest.TestSuite()

for t in testmodules:
	suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))

unittest.TextTestRunner().run(suite)