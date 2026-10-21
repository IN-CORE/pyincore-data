# Copyright (c) 2026 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import os
import requests
from urllib.parse import quote

# importing config loads a .env file, if there is one
from pyincore_data import config  # noqa: F401

CENSUS_API_KEY_ENV = "CENSUS_API_KEY"
CENSUS_API_KEY_SIGNUP_URL = "https://api.census.gov/data/key_signup.html"


class CensusApiKeyError(Exception):
    """Raised when the Census API key is missing or rejected by the Census API."""

    pass


class CensusApiUtil:
    """Helpers for building and sending requests to api.census.gov"""

    @staticmethod
    def get_api_key(api_key: str = None):
        """Get the Census API key from the argument or the CENSUS_API_KEY environment variable.

        Args:
            api_key (str): Census API key. Overrides the CENSUS_API_KEY environment variable.

        Returns:
            str: Census API key

        """
        key = api_key or os.getenv(CENSUS_API_KEY_ENV)
        if not key:
            raise CensusApiKeyError(
                f"Census API key is missing. Set the {CENSUS_API_KEY_ENV} environment variable "
                f"(or add it to a .env file), or pass api_key=. "
                f"Get a key at {CENSUS_API_KEY_SIGNUP_URL}"
            )
        return key

    @staticmethod
    def add_api_key(url: str, api_key: str = None):
        """Append the Census API key to a Census API url.

        Args:
            url (str): Census API url without a key
            api_key (str): Census API key. Overrides the CENSUS_API_KEY environment variable.

        Returns:
            str: Census API url with the key

        """
        key = CensusApiUtil.get_api_key(api_key)
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}key={quote(key, safe='')}"

    @staticmethod
    def request_json(url: str, api_key: str = None):
        """Request a Census API url with the key and return the parsed json.

        Args:
            url (str): Census API url without a key
            api_key (str): Census API key. Overrides the CENSUS_API_KEY environment variable.

        Returns:
            obj: Parsed json response

        """
        # the Census API answers a missing or invalid key with a 302 redirect to
        # missing_key.html or invalid_key.html, so don't follow redirects
        response = requests.get(
            CensusApiUtil.add_api_key(url, api_key), allow_redirects=False
        )
        if response.is_redirect:
            raise CensusApiKeyError(
                f"Census API key is missing or invalid. Check the {CENSUS_API_KEY_ENV} value. "
                f"Get a key at {CENSUS_API_KEY_SIGNUP_URL}"
            )

        if response.status_code != 200:
            raise Exception(
                f"Failed to download the data from Census API (status {response.status_code}). "
                f"Please check your parameters."
            )

        return response.json()
