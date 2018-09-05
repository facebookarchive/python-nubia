#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
#

import ast
import re
import setuptools
import sys

# To use a consistent encoding
from codecs import open
from os import path

assert sys.version_info >= (3, 6, 0), "python-nubia requires Python 3.6+"
from pathlib import Path # noqa E402

here = Path(__file__).parent


def get_long_description() -> str:
    with open(path.join(here, "README.md"), "r", encoding="utf-8") as fh:
        return fh.read()


def get_version() -> str:
    black_py = here / "nubia/__init__.py"
    _version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")
    with open(black_py, "r", encoding="utf8") as f:
        match = _version_re.search(f.read())
        version = match.group("version") if match is not None else '"unknown"'
    return str(ast.literal_eval(version))


try:
    from pipenv.project import Project
    from pipenv.utils import convert_deps_to_pip
except ImportError:

    print("pipenv has to be installed, use 'pip3 install pipenv'", file=sys.stderr)
    sys.exit(1)

pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile["packages"], r=False)
test_requirements = convert_deps_to_pip(pfile["dev-packages"], r=False)

setuptools.setup(
    name="python-nubia",
    version=get_version(),
    author="Ahmed Soliman",
    author_email="asoli@fb.com",
    description="A framework for building beautiful shells",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords="cli shell interactive framework",
    url="https://github.com/facebookincubator/python-nubia",
    packages=setuptools.find_packages(exclude=["sample", "docs", "tests"]),
    python_requires=">=3.6",
    install_requires=requirements,
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ),
)
