"""
Wall motion labeler.

Usage:
python ekg_cardiology_echo_narrative_wma.py
"""
import os
import pandas as pd
from pandas import Series
import re
import time
import numpy as np

root_dir = '../../../../..'
import sys
sys.path.append(root_dir)
import utils


def get_wm_features():
    """Define features used for wall motion"""
    # 'technically limited' feature is applied on the ENTIRE report (not just Conclusions and Left Ventricle)
    features = {
        'wall_segment': {
            # RWMA.
            # Identify AHA 17 segments and "regional"
            'group_prefix': 'w',
            'regex_list': [r'basal', r'mid', r'apical',
                    r'\banteroseptal\b', r'\banterior\b', r'\banterolateral\b',
                    r'\binferolateral\b', r'\binferior\b', r'\binferoseptal\b',
                    r'\bseptal\b', r'\banterior\b', r'\blateral\b', r'\bapex\b',
                    r'regional']
        },
        'left_ventricle':{
            # Identify left ventric{le, ular} wall motion/segment
            'group_prefix': 'lv',
            'regex_list': [r'left ventric\w+', r'wall']
        },
        'motion': {
            # AGFA values include 'normal', 'mild hypokinesis', 'moderate hypokinesis', 'severe hypokinesis',
            # 'akinesis', 'dyskinesis'.
            # We split these into two groups: motion (kinesis) and severity.
            'group_prefix': 'm',
            'regex_list': [r'hypokin\w+', r'dyskin\w+', r'akin\w+']
        },
        'severity': {
            'group_prefix': 's',
            'regex_list': [r'borderline', r'mild', r'moderate', r'severe', r'\bnormal\b']
        },
        'global_wma': {
            'group_prefix': 'g',
            'regex_list': [r'global', r'diffuse']
        },
        'past_wma': {
            'group_prefix': 'p',
            'regex_list': [r'previous', r'recovered', r'prior']
        }
    }

    return features


def get_lv_findings_conclusions(meta_fp, test=False):
    sql = """
        SELECT TOP (1000) [PAT_ID]
            ,[PAT_MRN_ID]
            ,[HSP_ACCOUNT_ID]
            ,[Order_Number]
            ,[Accession_Number]
            ,[Order_Description]
            ,[Procedure_Date]
            ,'Left Ventricle Findings' AS [Section]
            ,[Findings] AS Narrative
        FROM [Nightingale].[dbo].[ekg_cardiology_echo_findings]
        WHERE Section LIKE '%Left Ventricle%'

        UNION
        SELECT TOP (1000) [PAT_ID]
            ,[PAT_MRN_ID]
            ,[HSP_ACCOUNT_ID]
            ,[Order_Number]
            ,[Accession_Number]
            ,[Order_Description]
            ,[Procedure_Date]
            ,'Conclusions' AS [Section]
            ,[Conclusions] AS Narrative
        FROM [Nightingale].[dbo].[ekg_cardiology_echo_conclusions]
        """
    if not test:
        sql = sql.replace('TOP (1000)', '')

    conn = utils.get_nightingale_connection(meta_fp=meta_fp)
    df = pd.read_sql(sql, conn)
    return df


def add_feature_group(df, group_prefix, regex_list):
    group_feats = []
    for r in regex_list:
        # Clean column name by removing regex tokens 
        col_name = '{}_{}'.format(group_prefix, r.replace('\\b', '').replace('\\w+', ''))
        df[col_name] = df['Sentence'].str.contains(r, regex=True).astype(int)
        group_feats.append(col_name)
    
    # Add grouping for feature group
    df['has_{}'.format(group_prefix)] = np.where(df[group_feats].sum(axis=1) != 0, 1, 0)
    return df


def main(test=False):
    meta_fp = os.path.join(root_dir, 'meta.yml')

    # Get 'Left Ventricle' findings and 'Conclusion' section
    df = get_lv_findings_conclusions(meta_fp, test)

    # Split 'Narrative' into sentences
    s = df['Narrative'].str.lower().str.split(r'\.\s+|(\w)\.(\w)').apply(Series, 1).stack()
    s.index = s.index.droplevel(-1)
    s.name = 'Sentence'
    df = df.join(s)

    # Save original columns
    orig_columns = df.columns.tolist()

    # Get features used for wall motion
    features = get_wm_features()

    # Add features as columns
    for f in features:
        feature_group = features[f]
        df = add_feature_group(df, feature_group['group_prefix'], feature_group['regex_list'])

    # Get all features columns
    feat_columns = [c for c in df.columns if c not in orig_columns and c[:4] != 'has_']
    print('...created {} feature columns'.format(len(feat_columns)))
    group_columns = [c for c in df.columns if c not in orig_columns and c[:4] == 'has_']
    print('...created {} group columns'.format(len(group_columns)))

    # Save table
    table_dict = {
        'ekg_cardiology_echo_narrative_wma': df
    }
    utils.write_table(meta_fp, table_dict)

if __name__ == '__main__':
    main(test=False)
