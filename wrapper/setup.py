
# Build using 'python setup.py'
import distutils.sysconfig, os, sys
from distutils.core import setup, Extension
from Cython.Build import cythonize

from sage.env import SAGE_LOCAL, SAGE_ROOT

extra_link_args =  ['-L' + SAGE_LOCAL + '/lib']
extra_compile_args = ['-w', '-O2', '-std=c99']
include_dirs = [SAGE_LOCAL+'/include/csage', SAGE_LOCAL+'/include', SAGE_LOCAL+'/include/python2.7', SAGE_LOCAL+'/lib/python/site-packages/numpy/core/include', SAGE_ROOT+'/src/sage/ext', SAGE_ROOT+'/src', SAGE_ROOT+'/src/sage/gsl', '.']

ext_modules = [Extension('wrapper', ['wrapper.pyx'],
                     libraries=['gghlite', 'mpfr', 'gmp', 'gmpxx', 'stdc++', 'pari', 'm', 'ec', 'gsl', 'gslcblas', 'atlas', 'ntl', 'csage'],
                     library_dirs=[SAGE_LOCAL + '/lib/'],
                     extra_compile_args = extra_compile_args,
                     extra_link_args = extra_link_args,
                     include_dirs = include_dirs)]
					 
setup(ext_modules = cythonize(ext_modules, include_path = include_dirs))