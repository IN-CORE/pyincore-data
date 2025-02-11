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
    def assign_hazus_specific_structure_type_working(gdf, sensitivity_analysis=False, random=False):
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
                - exactmatch: 'Yes' if an exact match was found, 'No' if a fallback was used.
        """
        np.random.seed(1337)

        o2b_dict = NsiUtil.read_occ_building_mapping()

        guid = []
        struct_typ = []
        no_stories = []
        year_built = []
        dgn_lvl = []
        exact_match = []
        fallback_count = 0

        cnt_nan = 0
        for i, row in gdf.iterrows():
            # Create UUID for each building
            guid.append(str(uuid.uuid4()))
            year_built_ = row['med_yr_blt']
            no_stories_ = row['num_story']
            occ_type_ = row['occtype'].split('-')[0]
            exact_match_flag = "Yes"

            # Standardize RES3 types to a single 'RES3' category
            if "RES3" in occ_type_:
                occ_type_ = "RES3"

            if occ_type_ == 'RES1':
                struct_typ.append("W1")  # Assume W1 for now (Tables A17-A19)
                no_stories.append(no_stories_)
                year_built.append(year_built_)
                dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
                exact_match.append(exact_match_flag)
                continue
            if occ_type_ == 'RES2':
                struct_typ.append("MH")
                no_stories.append(no_stories_)
                year_built.append(year_built_)
                dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
                exact_match.append(exact_match_flag)
                continue

            # Determine sheet based on number of stories and year built
            if no_stories_ <= 3:
                sheet = 'LowRise-Pre1950' if year_built_ <= 1950 else (
                    'LowRise-1950-1970' if year_built_ <= 1970 else 'LowRise-Post1970')
            elif no_stories_ <= 7:
                sheet = 'MidRise-Pre1950' if year_built_ <= 1950 else (
                    'MidRise-1950-1970' if year_built_ <= 1970 else 'MidRise-Post1970')
            else:
                sheet = 'HighRise-Pre1950' if year_built_ <= 1950 else (
                    'HighRise-1950-1970' if year_built_ <= 1970 else 'HighRise-Post1970')

            # Ensure occupancy type exists in the mapping
            if occ_type_ not in o2b_dict[sheet].index:
                exact_match_flag = "No"
                print(f"Warning: '{occ_type_}' not found in sheet '{sheet}'")

                # Apply fallback logic (HighRise -> MidRise -> LowRise)
                fallback_hierarchy = {
                    'HighRise': 'MidRise',
                    'MidRise': 'LowRise'
                }
                fallback_applied = False
                for key, value in fallback_hierarchy.items():
                    if key in sheet:
                        fallback_sheet = sheet.replace(key, value)
                        if occ_type_ in o2b_dict[fallback_sheet].index:
                            print(f"Applying fallback: '{occ_type_}' found in '{fallback_sheet}' instead.")
                            sheet = fallback_sheet
                            fallback_applied = True
                            fallback_count += 1
                            break

                if not fallback_applied:
                    struct_typ.append(np.nan)
                    no_stories.append(np.nan)
                    year_built.append(np.nan)
                    dgn_lvl.append(np.nan)
                    exact_match.append(exact_match_flag)
                    cnt_nan += 1
                    continue

            row = o2b_dict[sheet].loc[occ_type_].dropna()

            # If row is empty, apply fallback again
            if row.empty:
                exact_match_flag = "No"
                print(f"Warning: No valid data for '{occ_type_}' in sheet '{sheet}'")
                struct_typ.append(np.nan)
                no_stories.append(np.nan)
                year_built.append(np.nan)
                dgn_lvl.append(np.nan)
                exact_match.append(exact_match_flag)
                cnt_nan += 1
                continue

            struct_types = row.index.values
            struct_type_probs = row.values / 100

            if len(struct_type_probs) == 0:
                print(f"Warning: No valid probabilities for '{occ_type_}' in sheet '{sheet}'")
                struct_typ.append(np.nan)
            else:
                struct_typ.append(np.random.choice(struct_types, p=struct_type_probs) if random else struct_types[
                    np.argmax(struct_type_probs)])

            no_stories.append(no_stories_)
            year_built.append(year_built_)
            dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
            exact_match.append(exact_match_flag)

        print(f"Total fallback occurrences: {fallback_count}")

        # Add new columns to GeoDataFrame
        gdf['guid'] = guid
        gdf['struct_typ'] = struct_typ
        gdf['no_stories'] = no_stories
        gdf['year_built'] = year_built
        gdf['dgn_lvl'] = dgn_lvl
        gdf['exact_match'] = exact_match

        return gdf

    @staticmethod
    def assign_hazus_specific_structure_type(gdf, sensitivity_analysis=False, random=False):
        """
        Function to map HAZUS-specific occupancy types to HAZUS-specific building types.
        Based on HAZUS 6.0 Inventory Technical Manual with some assumptions.

        Fallback Logic:
        - If an exact match for the occupancy type is not found in the primary sheet,
          the function applies a structured fallback mechanism.
        - The fallback hierarchy ensures that:
          - HighRise falls back to MidRise, then LowRise.
          - MidRise falls back to LowRise.
          - LowRise has no fallback.
        - If the occupancy type is found in a fallback sheet, it is used instead, and a
          warning is printed indicating the fallback action.
        - If no valid data is found even after fallback attempts, the function assigns NaN values.

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
                - exactmatch: 'Yes' if an exact match was found, 'No' if a fallback was used.
        """
        np.random.seed(1337)

        o2b_dict = NsiUtil.read_occ_building_mapping()

        guid = []
        struct_typ = []
        no_stories = []
        year_built = []
        dgn_lvl = []
        exact_match = []
        fallback_count = 0

        cnt_nan = 0
        for i, row in gdf.iterrows():
            guid.append(str(uuid.uuid4()))
            year_built_ = row['med_yr_blt']
            no_stories_ = row['num_story']
            occ_type_ = row['occtype'].split('-')[0]
            exact_match_flag = "Yes"

            if "RES3" in occ_type_:
                occ_type_ = "RES3"

            if occ_type_ == 'RES1':
                struct_typ.append("W1")
                no_stories.append(no_stories_)
                year_built.append(year_built_)
                dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
                exact_match.append(exact_match_flag)
                continue
            if occ_type_ == 'RES2':
                struct_typ.append("MH")
                no_stories.append(no_stories_)
                year_built.append(year_built_)
                dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
                exact_match.append(exact_match_flag)
                continue

            if no_stories_ <= 3:
                sheet = 'LowRise-Pre1950' if year_built_ <= 1950 else (
                    'LowRise-1950-1970' if year_built_ <= 1970 else 'LowRise-Post1970')
                fallback_sheets = []
            elif no_stories_ <= 7:
                sheet = 'MidRise-Pre1950' if year_built_ <= 1950 else (
                    'MidRise-1950-1970' if year_built_ <= 1970 else 'MidRise-Post1970')
                fallback_sheets = [
                    sheet.replace("MidRise", "LowRise"),
                    sheet.replace("MidRise", "LowRise").replace("1950-1970", "Pre1950")
                ]
            else:
                sheet = 'HighRise-Pre1950' if year_built_ <= 1950 else (
                    'HighRise-1950-1970' if year_built_ <= 1970 else 'HighRise-Post1970')
                fallback_sheets = [
                    sheet.replace("HighRise", "MidRise"),
                    sheet.replace("HighRise", "LowRise"),
                    sheet.replace("HighRise", "LowRise").replace("1950-1970", "Pre1950")
                ]

            found_match = False
            for check_sheet in [sheet] + fallback_sheets:
                if occ_type_ in o2b_dict.get(check_sheet, pd.DataFrame()).index:
                    row = o2b_dict[check_sheet].loc[occ_type_].dropna()
                    if not row.empty:
                        if check_sheet != sheet:
                            print(f"Warning: '{occ_type_}' not found in sheet '{sheet}'")
                            exact_match_flag = "No"
                            print(f"Applying fallback: '{occ_type_}' found in '{check_sheet}' instead.")
                            fallback_count += 1
                        sheet = check_sheet
                        found_match = True
                        break

            if not found_match:
                print(f"Warning: '{occ_type_}' not found in any applicable sheet.")
                struct_typ.append(np.nan)
                no_stories.append(np.nan)
                year_built.append(np.nan)
                dgn_lvl.append(np.nan)
                exact_match.append("No")
                cnt_nan += 1
                continue

            struct_types = row.index.values
            struct_type_probs = row.values / 100

            if len(struct_type_probs) == 0:
                print(f"Warning: No valid probabilities for '{occ_type_}' in sheet '{sheet}'")
                struct_typ.append(np.nan)
            else:
                struct_typ.append(np.random.choice(struct_types, p=struct_type_probs) if random else struct_types[
                    np.argmax(struct_type_probs)])

            no_stories.append(no_stories_)
            year_built.append(year_built_)
            dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))
            exact_match.append(exact_match_flag)

        print(f"Total fallback occurrences: {fallback_count}")
        print(f"Total empty rows: {cnt_nan}")

        gdf['guid'] = guid
        gdf['struct_typ'] = struct_typ
        gdf['no_stories'] = no_stories
        gdf['year_built'] = year_built
        gdf['dgn_lvl'] = dgn_lvl
        gdf['exact_match'] = exact_match

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
