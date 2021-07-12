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
    state_counties = ['01001', '01003']
    disloc_df, bgmap = CensusUtil.get_blockgroupdata_for_dislocation(state_counties)

    assert disloc_df['Survey'][0] == '2010 dec/sf1'
