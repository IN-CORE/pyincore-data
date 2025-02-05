import pandas as pd
import geopandas as gpd
import numpy as np
import os


class NsiUtil:
    @staticmethod
    def read_occ_building_mapping():
        # Path to the CSV directory
        csv_dir = os.path.join(os.getcwd(), 'data', 'nsi', 'occ_bldg_mapping')

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
    def assign_hazus_specific_structure_type(gdf, sensitivity_analysis=False, path_to_mapping=None, random=False):
        """
        Function to map HAZUS specific occupancy types to HAZUS specific building types
        Based on HAZUS 6.0 Inventory Technical Manual with some assumptions

        inputs:
            - gdf: geodataframe with NSI data
            - path_to_mapping: path to excel sheet with tables of specific
                occupancy types to building type probabilities;
                Tables A2-A10 in above HAZUS manual; these are west coast tables
            - random: boolean to decide whether to randomize mappings
                If true, building types are sampled using above probabiliteis
                If false, building types are based on highest probabilty (e.g. avg. of samples)
        """

        np.random.seed(1337)
        if path_to_mapping is None:
            raise ValueError("No path_to_mapping provided!")

        o2b_dict = NsiUtil.read_occ_building_mapping()

        guid = []
        struct_typ = []
        no_stories = []
        year_built = []
        dgn_lvl = []

        cnt_nan = 0
        for i, row in gdf.iterrows():
            guid.append(row['fd_id'])

            year_built_ = row['med_yr_blt']
            no_stories_ = row['num_story']
            occ_type_ = row['occtype'].split('-')[0]

            """ Assuming that all buildnigs with RES3 in them are "RES3" 
                e.g., RES3A, RES3B, RES3C, ...
                Here, A, B, C, etc. refer to the size of multi-family dwelling unit
                This could likely be refined
            """
            if "RES3" in occ_type_:
                occ_type_ = "RES3"

            # bldg_type_ = row['bldgtype']

            if occ_type_ == 'RES1':
                struct_typ.append("W1")  # for oregon, RES1 is 99% W1 and 1% RM1L; assuming W1 for now (Tables A17-A19)
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

            if no_stories_ <= 3:
                if year_built_ <= 1950:
                    sheet = 'LowRise-Pre1950'
                elif (year_built_ > 1950) & (year_built_ <= 1970):
                    sheet = 'LowRise-1950-1970'
                elif year_built_ > 1970:
                    sheet = 'LowRise-Post1970'
            elif (no_stories_ > 3) & (no_stories_ <= 7):
                if year_built_ <= 1950:
                    sheet = 'MidRise-Pre1950'
                elif (year_built_ > 1950) & (year_built_ <= 1970):
                    sheet = 'MidRise-1950-1970'
                elif year_built_ > 1970:
                    sheet = 'MidRise-Post1970'
            elif no_stories_ > 7:
                if year_built_ <= 1950:
                    sheet = 'HighRise-Pre1950'
                elif (year_built_ > 1950) & (year_built_ <= 1970):
                    sheet = 'HighRise-1950-1970'
                elif year_built_ > 1970:
                    sheet = 'HighRise-Post1970'

            if sensitivity_analysis:
                df_ = o2b_dict[sheet]  # getting specific sheet from excel doc
                df_ = df_.dropna(how='all')  # dropping rows where entire row is nan
                if occ_type_ in df_.index:  # if occupancy type is in the index
                    row = df_.loc[occ_type_]
                    row = row.dropna()  # dropping nan values from row
                    struct_types = row.index.values
                    struct_type_probs = row.values / 100
                else:  # occupancy type is not in excel sheet
                    struct_typ.append(np.nan)
                    no_stories.append(np.nan)
                    year_built.append(np.nan)
                    dgn_lvl.append(np.nan)
                    cnt_nan += 1
                    continue
            else:
                row = o2b_dict[sheet].loc[occ_type_]  # isolating relevant row in dataframe
                row = row.dropna()  # dropping nan values from row
                struct_types = row.index.values
                struct_type_probs = row.values / 100

            if random:
                struct_typ.append(np.random.choice(struct_types, p=struct_type_probs))
            elif not random:
                struct_typ.append(struct_types[np.argmax(struct_type_probs)])
            no_stories.append(no_stories_)
            year_built.append(year_built_)
            dgn_lvl.append(NsiUtil.year_built_to_dgn_lvl(year_built_))

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
