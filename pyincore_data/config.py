# Copyright (c) 2025 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

# configs file
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """
    class to list all configuration settings required for preprocessing and formatting for EddyPro and PyFluxPro
    """
    # database parameters
    DB_URL = os.getenv('DB_URL', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME')
    DB_USERNAME = os.getenv('DB_USERNAME')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    # NSI parameters
    NSI_URL_STATE = os.getenv('NSI_URL_STATE', 'https://nsi.sec.usace.army.mil/downloads/nsi_2022/')
    NSI_PREFIX = os.getenv('NSI_PREFIX', 'nsi_2022_')
    NSI_URL_FIPS = os.getenv('NSI_URL_FIPS', 'https://nsi.sec.usace.army.mil/nsiapi/structures?fips=')
    NSI_URL_FIPS_INTERNAL = os.getenv('NSI_URL_FIPS_INTERNAL', 'https://nsi.sec.usace.army.mil/internal/nsiapi/structures?fips=')
