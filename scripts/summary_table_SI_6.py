from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np


Path('final').mkdir(parents=True, exist_ok=True)
cols = ['MapName', 'num_lia', 'num_rgi', 'lia_area', 'rgi_area', 'diff_rgi', 'pct_chg']

mountain_table = gpd.read_file('final_v6/mountainregions.gpkg')
mountain_table = mountain_table[cols].sort_values('MapName').dropna().set_index('MapName')

# get the totals for each column
summary = mountain_table.agg(["sum"])

# remove the number totals due to double-counting
summary.loc['sum', ['num_lia', 'num_rgi']] = np.nan

# re-calculate the percent change using the totals
summary.loc['sum', 'pct_chg'] = 100 * summary.loc['sum', 'diff_rgi'] / summary.loc['sum', 'lia_area']

# append the total column to the table, save to csv
pd.concat([
    mountain_table,
    summary.rename(index={'sum': 'Total'})
]).to_csv(Path('final', 'Table_SI_6.csv'))
