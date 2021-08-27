# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

setup(
    name='pyincore-data',
    version='0.2.0',
    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={
        '': ['*.ini']
    },
    description='IN-CORE data python package',
    long_description="This package is designed for .",
    # TODO need to figure out what are the dependency requirements
    # TODO this is a hack, really should only be packages needed to run
    install_requires=[line.strip() for line in open("requirements.txt").readlines()],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering"
    ],
    keywords=[
        "data", "census"
    ],
    license="Mozilla Public License v2.0",
    url="https://git.ncsa.illinois.edu/incore/pyincore-data"
)