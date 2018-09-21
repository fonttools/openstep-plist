from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.sdist import sdist as _sdist
from distutils import log
import os
import pkg_resources
from io import open
import re


# check if minimum required Cython is available
cython_version_re = re.compile('\s*"cython\s*>=\s*([0-9][0-9\w\.]*)\s*"')
with open("pyproject.toml", "r", encoding="utf-8") as fp:
    for line in fp:
        m = cython_version_re.match(line)
        if m:
            cython_min_version = m.group(1)
            break
    else:
        sys.exit("error: could not parse cython version from pyproject.toml")
try:
    required_cython = "cython >= %s" % cython_min_version
    pkg_resources.require(required_cython)
except pkg_resources.ResolutionError:
    with_cython = False
else:
    with_cython = True


class cython_build_ext(_build_ext):
    """Compile *.pyx source files to *.c using cythonize if Cython is
    installed, else use the pre-generated *.c sources.
    """

    def finalize_options(self):
        if with_cython:
            from Cython.Build import cythonize

            # optionally enable line tracing for test coverage support
            linetrace = os.environ.get("CYTHON_TRACE") == "1"

            self.distribution.ext_modules[:] = cythonize(
                self.distribution.ext_modules,
                force=linetrace or self.force,
                annotate=os.environ.get("CYTHON_ANNOTATE") == "1",
                quiet=not self.verbose,
                compiler_directives={
                    "linetrace": linetrace,
                    "language_level": 3,
                    "embedsignature": True,
                },
            )
        else:
            log.warn(
                "%s not installed; using pre-generated *.c sources"
                % required_cython
            )
            for ext in self.distribution.ext_modules:
                ext.sources = [re.sub("\.pyx$", ".c", n) for n in ext.sources]

        _build_ext.finalize_options(self)


class cython_sdist(_sdist):
    """ Run 'cythonize' on *.pyx sources to ensure the *.c files included
    in the source distribution are up-to-date.
    """

    def run(self):
        if not with_cython:
            from distutils.errors import DistutilsSetupError
            raise DistutilsSetupError(
                "Cython >= %s is required to make sdist" % cython_min_version
            )

        from Cython.Build import cythonize

        cythonize(
            self.distribution.ext_modules,
            force=True,
            quiet=not self.verbose,
            compiler_directives={
                "language_level": 3,
                "embedsignature": True,
            }
        )
        _sdist.run(self)


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
    ext_modules=extensions,
    cmdclass={
        "build_ext": cython_build_ext,
        "sdist": cython_sdist,
    },
)
