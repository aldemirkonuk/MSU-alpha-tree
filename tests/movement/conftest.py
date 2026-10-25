"""Shared test setup for the movement-grammar suites.

DEF-T22 (defense changes_loop1 / L2-DEF-T22, closed in the 25 Oct minor-items pass): single-threaded BLAS for every
family before numpy is imported. Under a heavy machine load multithreaded BLAS made each small linear-algebra call in
mvlib.ca_rts pay a thread start-up, and one scene took ~16 s. The defense test file keeps its own setdefault as well.
"""
import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_k, "1")
