#lang C
#clib gghlite
#cargs -std=c99

### necessary when using setup.py? ###

#include "interrupt.pxi"  # ctrl-c interrupt block support

#include "cdefs.pxi"

include 'sage/ext/stdsage.pxi'

from gghlite cimport *
from sage.rings.ring cimport Ring
from sage.libs.mpfr cimport mpfr_free_cache
from sage.libs.flint.fmpz cimport fmpz_init, fmpz_init_set_ui, fmpz_clear, fmpz_get_str, fmpz_set_str
from sage.structure.element cimport ModuleElement, RingElement
from sage.categories.rings import Rings

from sage.libs.flint.fmpz_poly cimport fmpz_poly_init, fmpz_poly_clear, fmpz_poly_set_coeff_fmpz

from sage.rings.finite_rings.integer_mod cimport IntegerMod_gmp
	
cdef class Encoded_Element(RingElement):
	#remove when using setup.py
	cdef gghlite_enc_t value
	
	def __cinit__(self):
		pass
		
	def __init__(self, parent, x=0, level=0):
		RingElement.__init__(self, parent)
		
		#later assert that level is smaller than kappa!
		
		cdef Encoded_Parent prnt = <Encoded_Parent>parent
		
		sig_on()
		gghlite_enc_init(self.value, prnt.params)
		sig_off()
		
		cdef int rerand = 0

		cdef fmpz_t tmp_fmpz
		cdef fmpz_poly_t tmp_fmpz_poly
		
		fmpz_poly_init(tmp_fmpz_poly)
		#todo: change to something more sensible ? (how?^^)
		fmpz_set_str(tmp_fmpz, x.__repr__(), 10)
		sig_on()
		fmpz_poly_set_coeff_fmpz(tmp_fmpz_poly, 0, tmp_fmpz);
		gghlite_enc_set_gghlite_clr(self.value, prnt.instance, tmp_fmpz_poly, 1, level, rerand, prnt.randstate)
		sig_off()
		fmpz_clear(tmp_fmpz)
		fmpz_poly_clear(tmp_fmpz_poly)
		
	cdef Encoded_Element _new_c(self):
		cdef Encoded_Element x
		x = PY_NEW(Encoded_Element)
		x._parent = self._parent
		gghlite_enc_init(x.value, (<Encoded_Parent>self._parent).params)
		return x

	def __dealloc__(self):
		sig_on()
		gghlite_enc_clear(self.value)
		sig_off()
	
	def _repr_(self):
		return 'Encoding'
		
	cpdef ModuleElement _add_(self, ModuleElement right):
		cdef Encoded_Element ret
		ret = self._new_c()
		sig_on()
		gghlite_enc_add(ret.value, (<Encoded_Parent>self.parent()).params, self.value, (<Encoded_Element>right).value)
		sig_off()
		return ret
	
	cpdef RingElement _mul_(self, RingElement right):
		cdef Encoded_Element ret
		ret = self._new_c()
		sig_on()
		gghlite_enc_mul(ret.value, (<Encoded_Parent>self.parent()).params, self.value, (<Encoded_Element>right).value)
		sig_off()
		return ret
		
	cpdef ModuleElement _sub_(self, ModuleElement right):
		cdef Encoded_Element ret
		ret = self._new_c()
		sig_on()
		gghlite_enc_sub(ret.value, (<Encoded_Parent>self.parent()).params, self.value, (<Encoded_Element>right).value)
		sig_off()
		return ret
		
	def __nonzero__(self):
		sig_on()
		ret = not gghlite_enc_is_zero((<Encoded_Parent>self.parent()).params, self.value)
		sig_off()
		return ret
		
	#--- NOTES ---	
	#line 953 in element.pyx -> need to add __richcmp__ ?	
	#continue in 1230	
	
	#look at __richcmp__ again, some conditions there
	
cdef class Encoded_Parent(Ring):
	Element = Encoded_Element

	# remove when using setup.py
	cdef size_t kappa, lamb
	cdef fmpz_t p
	cdef gghlite_params_t params
	cdef flint_rand_t randstate
	
	cdef gghlite_sk_t instance
	
	def getP(self):
		return int(fmpz_get_str(NULL, 10, self.p))
	
	def __cinit__(self):
		fmpz_init(self.p)

	def __init__(self, base, kappa, lamb=20, mp_limb_t seed=0, category=None):
		print 'super init'
		# todo: might have to change Rings() to something more specific (see "Implementing the category framework for the parent")
		Ring.__init__(self, base, category=category or Rings())
		
		#cdef gghlite_sk_t instance
		cdef gghlite_flag_t flags
		
		self.kappa = kappa
		self.lamb = lamb
		
		flint_randinit_seed(self.randstate, seed, 1)
		
		# see gghlite-defs.h for more options
		flags = <gghlite_flag_t> (GGHLITE_FLAGS_GDDH_HARD | GGHLITE_FLAGS_VERBOSE | GGHLITE_FLAGS_GOOD_G_INV | GGHLITE_FLAGS_ASYMMETRIC)
		#flags = flags | GGHLITE_FLAGS_PRIME_G
		
		# initialize, get parameters and clear secret parameters
		sig_on()
		gghlite_init(self.instance, self.lamb, self.kappa, 1, flags, self.randstate)
		sig_off()
		print 'gghlite init complete'
		
		sig_on()
		gghlite_params_ref(self.params, self.instance)
		sig_off()
		print 'got params'
		
		sig_on()
		gghlite_sk_get_p(self.instance, self.p)
		sig_off()
		#print 'got p value: %i' % self.getP()
		
		#sig_on()
		#gghlite_sk_clear(instance, 0)
		#sig_off()
		#print 'gghlite sk clear complete'
	
	def __dealloc__(self):
		fmpz_clear(self.p)
		sig_on()
		gghlite_params_clear(self.params)
		flint_randclear(self.randstate)
		mpfr_free_cache()
		flint_cleanup()
		sig_off()
		pass
		
	def _repr_(self):
		return "Encoded_Parent(%s, kappa=%s, lamb=%s)"%(repr(self.base()), self.kappa, self.lamb)
		
	def base_ring(self):
		return self.base().base_ring()
		
	def characteristic(self):
		return self.base().characteristic()