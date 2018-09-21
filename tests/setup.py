import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from setup import cython_build_ext, include_dirs
from setuptools import setup, Extension


setup(
    ext_modules=[
        Extension(
            "tests.cdef_wrappers",
            sources=["tests/cdef_wrappers.pyx"],
            include_dirs=include_dirs,
        )
    ],
    cmdclass={"build_ext": cython_build_ext},
)
