from pathlib import Path
import geopandas as gpd
import pandas as pd


Path('final').mkdir(parents=True, exist_ok=True)
cols = ['MapName', 'lia_area', 'lia_ablation', 'dV_lia', 'mb_lia', 'mb_hugonnet', 'mb_acc', 'dM_lia', 'dM_hugonnet', 'rgi_area']

mountain_table = gpd.read_file('final/mountainregions.gpkg')
mountain_table = mountain_table[cols].sort_values('MapName').dropna().set_index('MapName')

# get the totals for each column
summary = mountain_table.agg(["sum"])

# re-calculate the percent change using the totals
summary.loc['sum', 'mb_acc'] = summary.loc['sum', 'mb_hugonnet'] / summary.loc['sum', 'mb_lia']

# append the total column to the table, save to csv
pd.concat([
    mountain_table,
    summary.rename(index={'sum': 'Total'})
]).to_csv(Path('final', 'Table_SI_7.csv'))
