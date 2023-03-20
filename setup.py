# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from setuptools import setup, find_packages

# version number of pyincore-data
version = '0.6.0'

with open("README.rst", encoding="utf-8") as f:
    readme = f.read()

setup(
    name='pyincore_data',
    version=version,
    description='IN-CORE data python package',
    long_description=readme,
    long_description_content_type='text/x-rst',
    
    url='https://incore.ncsa.illinois.edu',

    license="Mozilla Public License v2.0",

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
        "data",
        "census"
    ],

    packages=find_packages(where=".", exclude=["*.tests", "*.tests.*", "tests.*"]),
    include_package_data=True,
    package_data={
        '': ['*.ini']
    },

    python_requires=">=3.6",

    install_requires=[line.strip() for line in open("requirements.txt").readlines()],

    project_urls={
        'Bug Reports': 'https://github.com/IN-CORE/pyincore-data/issues',
        'Source': 'https://github.com/IN-CORE/pyincore-data',
    },
)
