from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.sdist import sdist as _sdist
from distutils import log
import os
import sys
import pkg_resources
from io import open
import re


argv = sys.argv[1:]
needs_wheel = {"bdist_wheel"}.intersection(argv)
wheel = ["wheel"] if needs_wheel else []

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
                include_path=["src"],
            )
        else:
            log.warn(
                "%s not installed; using pre-generated *.c sources" % required_cython
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
            compiler_directives={"language_level": 3, "embedsignature": True},
            include_path=["src"],
        )
        _sdist.run(self)


# need to include this for Visual Studio 2008 doesn't have stdint.h
include_dirs=(
    [os.path.join(os.path.dirname(__file__), "vendor", "msinttypes")]
    if os.name == "nt" and sys.version_info < (3,)
    else []
)

extensions = [
    Extension(
        "openstep_plist._parser",
        sources=["src/openstep_plist/_parser.pyx"],
        include_dirs=include_dirs,
    ),
]

with open("README.md", "r") as f:
    long_description = f.read()

version_file = os.path.join("src", "openstep_plist", "_version.py")

setup_args = dict(
    name="openstep_plist",
    use_scm_version={"write_to": version_file},
    description="ASCII plist parser written in Cython",
    author="Cosimo Lupo",
    author_email="cosimo@anthrotype.com",
    url="https://github.com/fonttools/openstep-plist",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    ext_modules=extensions,
    setup_requires=["setuptools_scm"] + wheel,
    cmdclass={"build_ext": cython_build_ext, "sdist": cython_sdist},
    zip_safe=False,
)


if __name__ == "__main__":
    setup(**setup_args)
