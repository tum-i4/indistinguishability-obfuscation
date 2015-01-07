=========
 Obfusc8 
=========
------------------------------------------------------------
Implementation of Candidate Indistinguishability Obfuscation
------------------------------------------------------------

This project is a preliminary implementation of the Candidate Indistinguishability Obfuscation algorithm recently proposed by Garg et al. [0].
Each of the steps necessary for the NC_1 candidate is implemented, but not all of them work completely. 
Especially the implementation of Multilinear Jigsaw Puzzles is still in the early phases of development and not fully functional.

[0] S. Garg, C. Gentry, S. Halevi, M. Raykova, A. Sahai, and B. Waters. "Candidate indistinguishability obfuscation and functional encryption for all circuits." In: Foundations of Computer Science (FOCS), 2013 IEEE 54th Annual Symposium on. IEEE. 2013, pp. 40-49.

Installation
============

All of the code is written in Python, using the libraries of the mathematical software Sage_ for the more advanced algebraic concepts.
Please refer to their website for installation instructions.

The experiments additionally require Guppy_ to be installed in the context of Sage. To do so either execute::
	
	sage --python -m easy_install guppy
	
or download and extract the tarball manually and execute::

	sage --python setup.py install

.. _Sage: http://www.sagemath.org/
.. _Guppy: https://pypi.python.org/pypi/guppy/0.1.10

Modules
=======

In the following a quick overview of the main modules.
Further documentation can be found in the docstring of each module.

* blocks: Building blocks for universal circuit creation
* bp: Matrix Branching Programs with 5x5 permutation matrices
* circuit: Logical circuits consisting of AND- and NOT-gates.
* generate_bp_mappings: Generate the mappings used in the fast Branching Program generation.
* mjp[1]: Attempt to implement the Multilinear Jigsaw Puzzles
* obf[1]: Putting together the different parts of the construction.
* rbp[1]: Randomized Branching Programs
* toposort: external package for topological sorting

.. [1] Requires sage

Each module can be run as a script by invoking::
	
	sage --python -m obfusc8.%modulename%
	
This will execute some example code showcasing the functionality of the respective module.

Tests
-----

There are some unittests that aim to ensure the proper functioning of the codebase.
To execute the tests for a specific module run::
	
	sage --python -m obfusc8.test.test_%modulename%
	
To invoke all tests run::
	
	sage --python -m obfusc8.test.test_all
	
Experiments
===========

There exist some experiments that can be used to gauge the cost of this obfuscation candidate implementation.
All results will be stored in a SQLite database called results.db.
Some intermediate results as well as detailed logs will be stored in subfolders of a newly created ``results`` folder.

Some of the parameters can be adjusted in the ``shared_parameters.py`` file.

generationExp
-------------

To be able to understand how difficult it is to generate the obfuscation of a given circuit, this experiment benchmarks each intermediate step of the complete candidate for different input parameters (aka number of gates and inputs).
Because of the magnitude of the growth, it is necessary to restrict the benchmark to very small values.

Start with::
	
	sage --python -m obfusc8.experiments.generationExp %ID%
	
%ID% can be a number or several numbers separated by a ','. When no ID is present all experiments will be run.

Experiment IDs:

* 0: generate all useful UCs up to a input size of 4
* 1: Generate BPs for 'small' UCs [(2, 1), (2,2), (3,2), (2,3), (3,3), (4,3)]
* 2: Generate RBPs for 'small' UCs with three different primes
* 3: fix BPs for 'small' UCs with one arbitrary circuit
* 4: generate one RBP with different matrix dimensions than 1 ([1, 2, 3, 4, 5, 10, 100])

Dependencies: (a -> b means a needs to be run before b)

0 -> 1 -> 2

1 -> 3

1 -> 4

executionExp
------------

To understand how costly the obfuscation is in terms of execution overhead, this experiments benchmarks the evaluation of different the different intermediate steps of the full construction.
This experiment requires that the according generation experiments have been run beforehand.
Start with::
	
	sage --python -m obfusc8.experiments.executionExp %ID%
	
ID can be a number or several numbers separated by a ','. When no ID is present all experiments will be run.

Experiment IDs:

* 0: Universal Circuit evaluation
* 1: Branching Program evaluation
* 2: Randomized Branching Program evaluation
* 3: Fixed Randomized Branching Program evaluation
* 4: Bigger RBP (generation experiment #4) evaluation

mjpExp
------

Trying to understand: how long does it take to a) setup the mjp, b) encode one element and c) add/multiply two elements.
Also investigates memory needed for setup and the growth of the encode elements.
Start with::

	sage --python -m obfusc8.experiments.mjpExp

Authors
=======

* Sebastian Banescu
* Martín Ochoa
* Nils Kunze
* Alexander Pretschner