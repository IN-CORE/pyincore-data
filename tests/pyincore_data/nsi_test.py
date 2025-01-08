# Copyright (c) 2025 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pytest

from pyincore_data.nsiutil import NSI


@pytest.fixture
def client():
    return pytest.client


def test_create_nsi_gdf_by_county_fips():
    fips = '15005'
    gdf = NSI.create_nsi_gdf_by_county_fips(fips)

    assert gdf.shape[0] > 0


def test_create_nsi_gdf_by_counties_fips_list():
    fips_list = ['15005', '29001', '01001']
    merged_gdf = NSI.create_nsi_gdf_by_counties_fips_list(fips_list)

    assert merged_gdf.shape[0] > 0


def test_get_county_fips_by_state():
    state = 'illinois'
    fips_list = NSI.get_county_fips_by_state(state)

    assert len(fips_list) > 0


if __name__ == '__main__':
    # test_create_nsi_gdf_by_county_fips()
    # test_create_nsi_gdf_by_counties_fips_list()
    test_get_county_fips_by_state()
