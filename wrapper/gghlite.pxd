from libc.stdint cimport uint64_t
from sage.libs.flint.types cimport *

cdef extern from "flint/flint.h":
	ctypedef struct flint_rand_s:
		pass
		
	ctypedef flint_rand_s flint_rand_t
	
	void flint_randclear(flint_rand_t state)
	void flint_cleanup()
	
cdef extern from "oz/flint-addons.h":
	inline void flint_randinit_seed(flint_rand_t randstate, mp_limb_t seed, int gmp)
	
cdef extern from "flint/fmpz_mod_poly.h":
	ctypedef struct fmpz_mod_poly_struct:
		pass
	
	ctypedef fmpz_mod_poly_struct fmpz_mod_poly_t

cdef extern from "gghlite/gghlite-defs.h":
	ctypedef fmpz_mod_poly_t gghlite_enc_t

cdef extern from "gghlite/gghlite.h":
	ctypedef struct gghlite_pk_t:
		pass

	ctypedef struct gghlite_t:
		pass
	
	#Initialise a new GGHLite instance.
	void gghlite_init(gghlite_t self, const size_t lamb, const size_t kappa, 
		const uint64_t rerand_mask, const uint64_t flags, flint_rand_t randstate)

	#Get a reference to the public parameters of ``op``.
	void gghlite_pk_ref(gghlite_pk_t rop, gghlite_t op)

	#Clear GGHLite public key.
	void gghlite_pk_clear(gghlite_pk_t self)

	#Clear GGHLite instance.
	void gghlite_clear(gghlite_t self, int clear_pk)

	#Initialise encoding to zero at level 0.
	void gghlite_enc_init(gghlite_enc_t op, const gghlite_pk_t self)

	#Elevate an encoding at levek `k'` to level `k` and re-randomise if requested.
	void gghlite_elevate(gghlite_enc_t rop, gghlite_pk_t self, gghlite_enc_t op, long k, long kprime, int rerand, flint_rand_t randstate)

	#Sample a new random encoding at levek `k`.
	void gghlite_sample(gghlite_enc_t rop, gghlite_pk_t self, long k, flint_rand_t randstate)

	#Encode level-0 encoding ``op`` at level `k`.
	void gghlite_enc(gghlite_enc_t rop, gghlite_pk_t self, gghlite_enc_t op, long k, int rerand, flint_rand_t randstate)

	#Compute `h = f*g`.
	void gghlite_mul(gghlite_enc_t h, const gghlite_pk_t self, const gghlite_enc_t f, const gghlite_enc_t g)

	void gghlite_add(gghlite_enc_t h, const gghlite_pk_t self, const gghlite_enc_t f, const gghlite_enc_t g)

	#Extract canonical string from ``op``
	void gghlite_extract(fmpz_poly_t rop, const gghlite_pk_t self, const gghlite_enc_t op)

	#Return 1 if op is an encoding of zero at level ?
	bint gghlite_is_zero(const gghlite_pk_t self, const gghlite_enc_t op)