# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pytest

from pyincore_data.censusutil import CensusUtil


@pytest.fixture
def client():
    return pytest.client


def test_get_blockgroupdata_for_dislocation():
    state_counties = ["01001", "01003"]
    disloc_df, bgmap, out_dataset = CensusUtil.get_blockgroupdata_for_dislocation(
        state_counties
    )

    assert disloc_df["Survey"][0] == "2010 dec/sf1"


def test_get_fips_by_state():
    fips = CensusUtil.get_fips_by_state("illinois")

    assert "NAME" in fips[0]


def test_get_fips_by_state_county():
    fips = CensusUtil.get_fips_by_state_county("illinois", "champaign")

    assert fips == "17019"


def test_national_ave_values():
    navs = CensusUtil.national_ave_values(year=2020)
    assert navs[1]["average"] == 0.644373548235299


def test_demographic_factors():
    state = "texas"
    county = "galveston"
    year = 2020
    fips = CensusUtil.get_fips_by_state_county(state=state, county=county)
    state_code = fips[:2]
    county_code = fips[2:]
    geo_type = "block%20group:*"
    social_vulnerability_dem_factors_df = CensusUtil.demographic_factors(
        state_code=state_code, county_code=county_code, year=year, geo_type=geo_type
    ).dropna()
    assert (
        social_vulnerability_dem_factors_df.loc[0]["GEO_ID"] == "1500000US481677243004"
    )
