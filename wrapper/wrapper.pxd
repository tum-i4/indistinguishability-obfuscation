
from gghlite cimport *
from sage.structure.element cimport RingElement
from sage.rings.ring cimport Ring

cdef class Encoded_Parent(Ring):
	cdef size_t kappa, lamb
	cdef gghlite_pk_t * publickey
	cdef flint_rand_t * randstate
	
cdef class Encoded_Element(RingElement):
	cdef gghlite_enc_t * value