from setuptools import setup, find_packages, Extension


setup(
    name="aplist",
    version="0.1.0.dev0",
    author="Cosimo Lupo",
    author_email="cosimo@anthrotype.com",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    ext_modules=[
        Extension("aplist._aplist", sources=["src/aplist/_aplist.pyx"]),
    ],
)
