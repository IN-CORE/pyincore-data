import pandas as pd
import uuid
import numpy as np
import os


class NsiUtil:
    @staticmethod
    def read_occ_building_mapping():
        """
        Create mapping dictionary by reading tables of specific occupancy types to building type probabilities;
        Tables A2-A10 in above HAZUS manual; these are west coast tables

        :return: dictionary of occupancy to building type
        """
        # Get the directory of the mapping csv files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_dir = os.path.join(script_dir, 'data', 'nsi', 'occ_bldg_mapping', 'westcoast')

        o2b_dict = {}  # Occupancy to building dictionary

        # Iterate over all CSV files in the directory
        for filename in os.listdir(csv_dir):
            if filename.endswith(".csv"):
                sheet_name = filename.replace(".csv", "")  # Extract the original sheet name
                file_path = os.path.join(csv_dir, filename)

                # Read CSV file
                df = pd.read_csv(file_path)

                # Clean 'OccClass' column
                df['OccClass'] = df['OccClass'].apply(lambda x: str(x).replace(u'\xa0', u''))
                df.set_index('OccClass', inplace=True)

                # Clean column names
                old_cols = list(df.columns)
                new_cols = [str(x).replace(u'\xa0', u'') for x in old_cols]
                rename_dict = dict(zip(old_cols, new_cols))
                df.rename(columns=rename_dict, inplace=True)

                o2b_dict[sheet_name] = df

        return o2b_dict

    @staticmethod
    def assign_hazus_specific_structure_type(gdf, sensitivity_analysis=False, random=False):
        """
        Function to map HAZUS-specific occupancy types to HAZUS-specific building types.
        Based on HAZUS 6.0 Inventory Technical Manual with some assumptions.

        Inputs:
            - gdf: GeoDataFrame containing NSI data.
            - sensitivity_analysis (bool): If True, uses sensitivity analysis for structural type selection.
            - random (bool): If True, selects a building type randomly based on probability distribution;
                             otherwise, selects the type with the highest probability.

        Returns:
            GeoDataFrame with added columns:
                - guid: Unique identifier for each building.
                - struct_typ: Assigned structural type.
                - no_stories: Number of stories in the building.
                - year_built: Year the building was built.
                - dgn_lvl: Seismic design level.
        """
        np.random.seed(1337)

        # o2b_dict = NsiUtil.read_occ_building_mapping()
        o2b_dict = {}  # occupancy to building dictionary
        script_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(script_dir, 'data', 'nsi', 'occ_bldg_mapping', 'westcoast', 'OccBldgMapping.xlsx')
        xls = pd.ExcelFile(map_path)
        for sheet in xls.sheet_names:
            o2b_dict[sheet] = pd.read_excel(xls, sheet)  # , index_col=0)
            o2b_dict[sheet]['OccClass'] = o2b_dict[sheet]['OccClass'].apply(lambda x: str(x).replace(u'\xa0', u''))
            o2b_dict[sheet].set_index('OccClass', inplace=True)

            # column names had '\xa0' in them; replacing here
            old_cols = list(o2b_dict[sheet].columns)
            new_cols = [str(x).replace(u'\xa0', u'') for x in old_cols]
            rename_dict = dict(zip(old_cols, new_cols))
            o2b_dict[sheet].rename(columns=rename_dict, inplace=True)
        guid = []
        struct_typ = []
        no_stories = []
        year_built = []
        dgn_lvl = []

        cnt_nan = 0
        for i, row in gdf.iterrows():
            # Create UUID for each building
            guid.append(str(uuid.uuid4()))
            year_built_ = row['med_yr_blt']
            no_stories_ = row['num_story']
            occ_type_ = row['occtype'].split('-')[0]

            # Standardize RES3 types to a single 'RES3' category
            if "RES3" in occ_type_:
                occ_type_ = "RES3"

            if occ_type_ == 'RES1':
                struct_typ.append("W1")  # Assume W1 for now (Tables A17-A19)
                no_stories.append(no_stories_)
                year_built.append(year_built_)
                dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
                continue
            if occ_type_ == 'RES2':
                struct_typ.append("MH")
                no_stories.append(no_stories_)
                year_built.append(year_built_)
                dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
                continue

            # Determine sheet based on number of stories and year built
            if no_stories_ <= 3:
                sheet = 'LowRise-Pre1950' if year_built_ <= 1950 else ('LowRise-1950-1970' if year_built_ <= 1970 else 'LowRise-Post1970')
            elif no_stories_ <= 7:
                sheet = 'MidRise-Pre1950' if year_built_ <= 1950 else ('MidRise-1950-1970' if year_built_ <= 1970 else 'MidRise-Post1970')
            else:
                sheet = 'HighRise-Pre1950' if year_built_ <= 1950 else ('HighRise-1950-1970' if year_built_ <= 1970 else 'HighRise-Post1970')

            # Ensure occupancy type exists in the mapping
            if occ_type_ not in o2b_dict[sheet].index:
                print(f"Warning: '{occ_type_}' not found in sheet '{sheet}'")
                struct_typ.append(np.nan)
                no_stories.append(np.nan)
                year_built.append(np.nan)
                dgn_lvl.append(np.nan)
                cnt_nan += 1
                continue

            row = o2b_dict[sheet].loc[occ_type_].dropna()

            # If row is empty, avoid processing further
            if row.empty:
                print(f"Warning: No valid data for '{occ_type_}' in sheet '{sheet}'")
                struct_typ.append(np.nan)
                no_stories.append(np.nan)
                year_built.append(np.nan)
                dgn_lvl.append(np.nan)
                cnt_nan += 1
                continue

            struct_types = row.index.values
            struct_type_probs = row.values / 100

            if len(struct_type_probs) == 0:
                print(f"Warning: No valid probabilities for '{occ_type_}' in sheet '{sheet}'")
                struct_typ.append(np.nan)
            else:
                struct_typ.append(np.random.choice(struct_types, p=struct_type_probs) if random else struct_types[np.argmax(struct_type_probs)])

            no_stories.append(no_stories_)
            year_built.append(year_built_)
            dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))

        # Add new columns to GeoDataFrame
        gdf['guid'] = guid
        gdf['struct_typ'] = struct_typ
        gdf['no_stories'] = no_stories
        gdf['year_built'] = year_built
        gdf['dgn_lvl'] = dgn_lvl

        return gdf

    @staticmethod
    def year_built_to_dgn_lvl(year_built):
        if year_built < 1979:
            return "Pre - Code"
        elif (year_built >= 1979) & (year_built < 1995):
            return "Low - Code"
        elif (year_built >= 1995) & (year_built < 2003):
            return "Moderate - Code"
        elif year_built >= 2003:
            return "High - Code"
