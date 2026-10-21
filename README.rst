pyincore-data
=============

**pyIncore-data** is a component of IN-CORE. It is a python package containing utilities to prepare data for IN-CORE analyses.


Installation with conda
-----------------------

Installing **pyincore-data** with Conda is officially supported by IN-CORE development team. 

To add `conda-forge <https://conda-forge.org/>`__  channel to your environment, run

.. code-block:: console

   conda config –-add channels conda-forge

To install **pyincore-data** package, run

.. code-block:: console

   conda install -c in-core pyincore-data


To update **pyIncore-data**, run

.. code-block:: console

   conda update -c in-core pyincore-data


Installation with pip
-----------------------

Installing **pyincore-data** with pip is **NOT supported** by IN-CORE development team.
Please use pip for installing pyincore-data at your discretion. 

**Installing pyincore-data with pip is only tested on linux environment.**

To install **pyincore-data** package, run

.. code-block:: console

   pip install pyincore-data


Census API key
--------------

The Census methods in ``CensusUtil`` and the FIPS lookups in ``NsiParser`` call the
`Census Data API <https://api.census.gov/data.html>`_, which requires an API key.
Request a free key at https://api.census.gov/data/key_signup.html (the key is emailed to you
and must be activated from the link in that email), then set it as an environment variable

.. code-block:: console

   export CENSUS_API_KEY=your_key

or add ``CENSUS_API_KEY=your_key`` to a ``.env`` file in your working directory.
You can also pass the key directly, e.g. ``CensusUtil.get_fips_by_state("illinois", api_key="your_key")``.

Tests that call the Census API are skipped when ``CENSUS_API_KEY`` is not set.

**Prerequisite**

* For developers, pre-install must be installed. If not, run `brew install pre-commit` or `pip install pre-commit`.