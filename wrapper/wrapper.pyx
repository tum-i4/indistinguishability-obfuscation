#lang C
#clib gghlite
#cargs -std=c99

### necessary when using setup.py? ###

#include "interrupt.pxi"  # ctrl-c interrupt block support
#include "stdsage.pxi"  # ctrl-c interrupt block support

#include "cdefs.pxi"

from gghlite cimport *
from sage.rings.ring cimport Ring
from sage.libs.mpfr cimport mpfr_free_cache
from sage.structure.element cimport ModuleElement, RingElement
from sage.categories.rings import Rings
from cpython.mem cimport PyMem_Malloc, PyMem_Free

cdef class Encoded_Element(RingElement):
	#remove when using setup.py
	cdef gghlite_enc_t * value
	
	def __cinit__(self):
		self.value = <gghlite_enc_t *>PyMem_Malloc(sizeof(gghlite_enc_t))
		if not self.value:
			raise MemoryError()
	
	def __init__(self, parent, x=0):
		RingElement.__init__(self, parent)
		sig_on()
		gghlite_enc_init(self.value[0], (<Encoded_Parent>parent).publickey[0])
		sig_off()
		sig_on()
		gghlite_sample(self.value[0], (<Encoded_Parent>parent).publickey[0], 0, (<Encoded_Parent>parent).randstate[0])
		sig_off()
		
	def __dealloc__(self):
		PyMem_Free(self.value)
	
	def _repr_(self):
		return '--- PLACEHOLDER ---'
		
	cpdef ModuleElement _add_(self, ModuleElement right):
		cdef Encoded_Element ret = Encoded_Element(self.parent())
		sig_on()
		gghlite_add(ret.value[0], (<Encoded_Parent>self.parent()).publickey[0], self.value[0], (<Encoded_Element>right).value[0])
		sig_off()
		return ret
	
	cpdef RingElement _mul_(self, RingElement right):
		cdef Encoded_Element ret = Encoded_Element(self.parent())
		sig_on()
		gghlite_mul(ret.value[0], (<Encoded_Parent>self.parent()).publickey[0], self.value[0], (<Encoded_Element>right).value[0])
		sig_off()
		return ret
		
	def __nonzero__(self):
		sig_on()
		ret = not gghlite_is_zero((<Encoded_Parent>self.parent()).publickey[0], self.value[0])
		sig_off()
		return ret
		
	#--- NOTES ---	
	#line 953 in element.pyx -> need to add __richcmp__ ?	
	#continue in 1230	
	
	#look at __richcmp__ again, some conditions there

cdef class Encoded_Parent(Ring):
	Element = Encoded_Element

	#remove when using setup.py
	cdef size_t kappa, lamb
	cdef gghlite_pk_t * publickey
	cdef flint_rand_t * randstate
	
	def __cinit__(self):
		self.publickey = <gghlite_pk_t *>PyMem_Malloc(sizeof(gghlite_pk_t))
		self.randstate = <flint_rand_t *>PyMem_Malloc(sizeof(flint_rand_t))
		if not self.publickey or not self.randstate:
			raise MemoryError()
	
	def __init__(self, base, kappa, lamb=20, mp_limb_t seed=0, category=None):
		print 'super init'
		#todo: might have to change Rings() to something more specific (see "Implementing the category framework for the parent")
		Ring.__init__(self, base, category=category or Rings())
		
		cdef gghlite_t instance
		cdef uint64_t flags
		
		self.kappa = kappa
		self.lamb = lamb
		
		sig_on()
		flint_randinit_seed(self.randstate[0], seed, 1)
		sig_off()
		
		#default for now, see gghlite-defs.h for more options
		flags = 0
		
		sig_on()
		#initialize, get publickey and clear secret parameters
		gghlite_init(instance, self.lamb, self.kappa, 1, flags, self.randstate[0])
		sig_off()
		print 'gghlite init complete'
		sig_on()
		gghlite_pk_ref(self.publickey[0], instance)
		sig_off()
		print 'got public key'
		sig_on()
		gghlite_clear(instance, 0)
		sig_off()
		print 'gghlite clear complete'
	
	def __dealloc__(self):
		sig_on()
		if self.publickey is not NULL: gghlite_pk_clear(self.publickey[0])
		if self.randstate is not NULL: flint_randclear(self.randstate[0])
		mpfr_free_cache()
		flint_cleanup()
		sig_off()
		PyMem_Free(self.publickey)
		PyMem_Free(self.randstate)
		pass
		
	def _repr_(self):
		return "Encoded_Parent(%s, kappa=%s, lamb=%s)"%(repr(self.base()), self.kappa, self.lamb)
		
	def base_ring(self):
		return self.base().base_ring()
		
	def characteristic(self):
		return self.base().characteristic()