# Copyright (c) 2026 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

from unittest import mock

import pytest

from pyincore_data.utils.censusapiutil import CensusApiUtil, CensusApiKeyError

URL = "https://api.census.gov/data/2010/dec/sf1?get=NAME&for=county:*"


def _response(status_code, is_redirect=False, json_data=None):
    response = mock.Mock(status_code=status_code, is_redirect=is_redirect)
    response.json.return_value = json_data
    return response


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("CENSUS_API_KEY", raising=False)
    with pytest.raises(CensusApiKeyError, match="CENSUS_API_KEY"):
        CensusApiUtil.get_api_key()


def test_key_from_env(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "envkey")
    assert CensusApiUtil.add_api_key(URL) == URL + "&key=envkey"


def test_key_argument_overrides_env(monkeypatch):
    monkeypatch.setenv("CENSUS_API_KEY", "envkey")
    assert CensusApiUtil.add_api_key(URL, "argkey") == URL + "&key=argkey"


def test_add_key_without_query_string():
    url = "https://api.census.gov/data/2010/dec/sf1"
    assert CensusApiUtil.add_api_key(url, "k") == url + "?key=k"


def test_redirect_raises_key_error():
    with mock.patch(
        "pyincore_data.utils.censusapiutil.requests.get",
        return_value=_response(302, is_redirect=True),
    ) as get:
        with pytest.raises(CensusApiKeyError, match="missing or invalid"):
            CensusApiUtil.request_json(URL, "badkey")
    get.assert_called_once_with(URL + "&key=badkey", allow_redirects=False)


def test_non_200_raises():
    with mock.patch(
        "pyincore_data.utils.censusapiutil.requests.get",
        return_value=_response(400),
    ):
        with pytest.raises(Exception, match="status 400"):
            CensusApiUtil.request_json(URL, "k")


def test_success_returns_json():
    data = [["NAME", "state", "county"], ["Champaign County, Illinois", "17", "019"]]
    with mock.patch(
        "pyincore_data.utils.censusapiutil.requests.get",
        return_value=_response(200, json_data=data),
    ):
        assert CensusApiUtil.request_json(URL, "k") == data
