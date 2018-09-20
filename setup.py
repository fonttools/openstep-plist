from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize
import os


extensions = [
    Extension("aplist._aplist", sources=["src/aplist/_aplist.pyx"]),
]

setup(
    name="aplist",
    version="0.1.0.dev0",
    author="Cosimo Lupo",
    author_email="cosimo@anthrotype.com",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    ext_modules=cythonize(
        extensions,
        annotate=os.environ.get("CYTHON_ANNOTATE") == "1",
        compiler_directives={
            "language_level": 3,
            "linetrace": os.environ.get("CYTHON_TRACE") == "1",
            "embedsignature": True,
        }
    ),
)
