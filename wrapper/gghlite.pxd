from libc.stdint cimport uint64_t
from sage.libs.flint.types cimport *

cdef extern from "flint/flint.h":
	ctypedef struct flint_rand_s:
		pass
	ctypedef flint_rand_s flint_rand_t[1]
	
	void flint_randclear(flint_rand_t state)
	void flint_cleanup()
	
cdef extern from "flint/fmpz_mod_poly.h":
	ctypedef struct fmpz_mod_poly_struct:
		pass
	ctypedef fmpz_mod_poly_struct fmpz_mod_poly_t[1]
	
cdef extern from "oz/flint-addons.h":
	inline void flint_randinit_seed(flint_rand_t randstate, mp_limb_t seed, int gmp)

cdef extern from "gghlite/gghlite-defs.h":
	ctypedef fmpz_mod_poly_t gghlite_enc_t
	ctypedef fmpz_poly_t gghlite_clr_t
	ctypedef struct _gghlite_params_struct:
		pass
	ctypedef _gghlite_params_struct gghlite_params_t[1]
	ctypedef struct _gghlite_sk_struct:
		pass
	ctypedef _gghlite_sk_struct gghlite_sk_t[1]
	ctypedef enum gghlite_flag_t:
		GGHLITE_FLAGS_DEFAULT
		GGHLITE_FLAGS_PRIME_G
		GGHLITE_FLAGS_VERBOSE
		GGHLITE_FLAGS_GDDH_HARD
		GGHLITE_FLAGS_ASYMMETRIC
		GGHLITE_FLAGS_QUIET
		GGHLITE_FLAGS_GOOD_G_INV
		
cdef extern from "gghlite/gghlite.h":
	
	#--- instance stuff ---
	
	#Initialise a new GGHLite instance.
	void gghlite_init(gghlite_sk_t self, const size_t lamb, const size_t kappa,
		const uint64_t rerand_mask, const gghlite_flag_t flags, flint_rand_t randstate)

	# get p value
	void gghlite_sk_get_p(gghlite_sk_t self, fmpz_t p)
		
	#Get a shallow copy of `params` of `op`.
	void gghlite_params_ref(gghlite_params_t rop, gghlite_sk_t op)
	
	#Clear GGHLite `params`.
	void gghlite_params_clear(gghlite_params_t self)
		
	#Clear GGHLite instance.
	void gghlite_sk_clear(gghlite_sk_t self, int clear_params)

	#--- encoding stuff ---
	
	#Initialise encoding to zero at level 0.
	void gghlite_enc_init(gghlite_enc_t op, const gghlite_params_t self)
	
	void gghlite_enc_clear(gghlite_enc_t op)
	
	#Rerandomise encoding at level $k$ in group $G_i$.
	void gghlite_enc_rerand(gghlite_enc_t rop, const gghlite_params_t self, const gghlite_enc_t op,
		size_t k, size_t i, flint_rand_t randstate)
	
	# Raise encoding at level $k$ to level $l$ and re-randomise if requested.
	void gghlite_enc_raise(gghlite_enc_t rop, const gghlite_params_t self, const gghlite_enc_t op,
		size_t l, size_t k, size_t i, int rerand, flint_rand_t randstate)
	
	# Set `op` to an encoding of $c$ at level $k$ in group $G_i$.	
	void gghlite_enc_set_ui(gghlite_enc_t op, unsigned long c, const gghlite_params_t self,
		const size_t k, const size_t i, const int rerand, flint_rand_t randstate)
	
	# Sample a new random encoding at levek $k$ in group $i$.
	void gghlite_enc_sample(gghlite_enc_t rop, gghlite_params_t self, size_t k, size_t i, flint_rand_t randstate)
	
	# Encode $f$ at level-$k$ in group $G_i$.
	void gghlite_enc_set_gghlite_clr(gghlite_enc_t rop, const gghlite_sk_t self, const gghlite_clr_t f,
		const size_t k, const size_t i, const int rerand, flint_rand_t randstate)
	
	# Compute h = f (*/+/-) g.
	void gghlite_enc_mul(gghlite_enc_t h, const gghlite_params_t self, const gghlite_enc_t f, const gghlite_enc_t g)
	void gghlite_enc_add(gghlite_enc_t h, const gghlite_params_t self, const gghlite_enc_t f, const gghlite_enc_t g)
	void gghlite_enc_sub(gghlite_enc_t h, const gghlite_params_t self, const gghlite_enc_t f, const gghlite_enc_t g)
	
	#Extract canonical string from $f$
	void gghlite_enc_extract(fmpz_poly_t rop, const gghlite_params_t self, const gghlite_enc_t f)
	
	#Return 1 if $f$ is an encoding of zero at level $?$
	bint gghlite_enc_is_zero(const gghlite_params_t self, const gghlite_enc_t op)