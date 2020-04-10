"""Setup file for commonlib."""

import pathlib
import setuptools


# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setuptools.setup(
    name="ac",
    version="1.0.0",
    description="hJOP AC client",
    long_description=README,
    long_description_content_type="text/x-md",
    url="https://github.com/kmzbrnoI/ac-python",
    author="Jan Horacek",
    author_email="jan.horacek@kmz-brno.cz",
    license="Apache",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python"
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.7"
)
