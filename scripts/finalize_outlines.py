from pathlib import Path
from datetime import datetime
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from glacmaptools import utils
from glacmaptools.geometry import GlacierOutlines


def add_rgi_outline_dates(row: gpd.GeoSeries, rgi_outlines: GlacierOutlines, version: str) -> datetime.date:
    """
    Get the average RGI outline date, formatted as a datetime.date, for a given glacier outline.

    :param row: a geopandas GeoSeries corresponding to an individual glacier (i.e., a row of a GeoDataFrame)
    :param rgi_outlines: a GlacierOutlines corresponding to the RGI outlines for the given region
    :param version: the RGI version being used [either v6.0 or v7.0]
    :return: the average RGI outline source date
    """
    assert version in ['v6.0', 'v7.0']

    date_col = {'v6.0': 'BgnDate', 'v7.0': 'src_date'}

    if row['num_other'] == 0:
        return pd.to_datetime('2000-01-01').date()
    else:
        rgi_ids = row['other_inds'].split(',')
        dates = rgi_outlines.ds.loc[rgi_outlines['RGIId'].isin(rgi_ids), 'BgnDate'].values
        date_ints = pd.Series([pd.to_datetime(dd, format='%Y%m%d') for dd in dates]).astype(np.int64)
        return pd.to_datetime(date_ints.mean()).date()


# set different parameters based on which version of the RGI we're using (v6.0 or v7.0)
rgi_dict = {
    'v6.0': {
        'rgi_id': 'RGIId',
        'o2_shp': Path('00_rgi60_regions') / '00_rgi60_O2Regions.shp',
        'o2_name': 'RGI_CODE'
    },

    'v7.0': {
        'rgi_id': 'rgi_id',
        'o2_shp': Path('RGI2000-v7.0-regions') / 'RGI2000-v7.0-o2regions.shp',
        'o2_name': 'o2region'
    }
}

# load the config file, check the RGI directory and
# version name and create the output directory
with open('config.json') as src:
    config = json.load(src)

    assert Path(config['rgi_base']).exists(), f"RGI base directory: {Path(config['rgi_base'])} not found."
    assert config['rgi_ver'] in ['v6.0', 'v7.0'], "rgi_ver must be one of (v6.0, v7.0)"

    rgi_id = rgi_dict[config['rgi_ver']]['rgi_id']

    print(f"Using RGI {config['rgi_ver']}")
    print(f"Reading RGI files from: {Path(config['rgi_base']) / config['rgi_ver']}")

    # create output directory
    Path(config['outdir']).mkdir(parents=True, exist_ok=True)

# load the LIA outlines for southern Alaska
lia_outlines = GlacierOutlines(Path(config['srcdir']) / 'lia_outlines_alaska.gpkg')

# load mapped disconnections and mountain regions
disconnects = gpd.read_file(Path(config['srcdir']) / 'lia_disconnections.gpkg')
regions = GlacierOutlines(Path(config['srcdir']) / 'mountainregions.gpkg')

# sort glaciers by mountain ranges, then create a unique LIA ID and calculate LIA area (in square km)
# get glacier centroids (representative points)
centers = GlacierOutlines(lia_outlines.to_crs(6393).representative_point().to_crs(4326))

reg_ids = centers.sjoin(regions)['index_right'] # mountain region IDs that each glacier centroid belongs to
lia_outlines['reg_id'] = reg_ids

lia_outlines.ds.sort_values('reg_id', inplace=True) # sort by region
lia_outlines.ds.reset_index(drop=True, inplace=True) # reset index after sort
lia_outlines.reindex(prefix='LIA-01') # create a unique LIA ID for each outline

lia_outlines['area_km2'] = lia_outlines.to_crs(6393).geometry.area / 1e6 # area in sq km

# check that the regions fully cover the outlines, but only if we're doing RGI v6.0 (v7.0 added 2 glaciers)
outside = lia_outlines.union_all().difference(regions.union_all())

if config['rgi_ver'] == 'v6.0' and not outside.is_empty.all():
    Path(config['errdir']).mkdir(parents=True, exist_ok=True)
    outside.to_file(Path(config['errdir']) / 'outside_region.gpkg')
    raise ValueError("Region boundaries do not fully encompass LIA outlines. Check outside_region.gpkg and edit boundaries.")

# get the internal boundaries (ice divides) and save it to a file
borders_all = lia_outlines.interior_boundaries(line_only=True)
borders_all.to_file(Path(config['outdir']) / 'lia_interior_boundaries.gpkg')

# calculate the difference between the LIA outlines and all RGI outlines whose
# centroids fall within the LIA outlines, regardless of whether the RGI outlines
# are larger than 1 sq. km or not:
diff_all = lia_outlines.compute_rgi_area_change(rgi_reg=1,
                                                rgi_dir=Path(config['rgi_base']) / config['rgi_ver'],
                                                version=config['rgi_ver'],
                                                crs=6393)

diff_all['pct_chg'] = 100 * diff_all['area_change'] / diff_all['area'] # percent change for all glaciers, LIA - RGI

diff_all['reg_id'] = lia_outlines['reg_id']

# next, load the RGI outlines and sub-set them, to only include glaciers with an area of 1 sq. km.
# Then, calculate the difference between those outlines and the LIA outlines.
rgi_all = GlacierOutlines(utils.rgi_loader(rgi_reg=1,
                                           rgi_dir=Path(config['rgi_base']) / config['rgi_ver'],
                                           version=config['rgi_ver']))
rgi_sub = rgi_all[rgi_all['Area'] > 1].copy()

# add the average RGI date to the outlines
diff_all['rgi_date'] = diff_all.ds.apply(add_rgi_outline_dates, axis=1, rgi_outlines=rgi_all, version=config['rgi_ver'])

diff_sub = lia_outlines.compute_area_change(rgi_sub, crs=6393, other_id=rgi_id, keep_missing=False)
diff_sub['pct_chg'] = 100 * diff_sub['area_change'] / diff_sub['area']

# re-name a bunch of columns to make combining them easier
diff_all.ds = diff_all.ds.rename(columns={'area': 'lia_area', 'other_area': 'rgi_area',
                                          'area_change': 'diff_rgi', 'num_other': 'num_rgi',
                                          'pct_chg': 'pct_chg'})

diff_sub.ds = diff_sub.ds.rename(columns={'other_area': 'rgi_area_sub',
                                          'area_change': 'diff_rgi_sub', 'num_other': 'num_rgi_sub',
                                          'pct_chg': 'pct_chg_sub'})
diff_sub.ds.drop(columns=['area', 'geometry', 'other_inds'], inplace=True) # drop these columns from the subset

# join the two tables together and fill in missing values with a 0
difference = diff_all.ds.join(diff_sub.ds)

sub_cols = ['rgi_area_sub', 'diff_rgi_sub', 'num_rgi_sub']
difference[sub_cols] = difference[sub_cols].fillna(0)
difference['num_rgi_sub'] = difference['num_rgi_sub'].astype(int)

lookup_table = difference[['other_inds']]
lookup_table.to_csv(Path(config['outdir']) / f"lia_rgi{config['rgi_ver']}_lookup.csv")

difference.drop(columns=['other_inds'], inplace=True)

columns = ['lia_id', 'lia_area', 'rgi_date',
           'rgi_area', 'diff_rgi',
           'num_rgi', 'pct_chg',
           'rgi_area_sub', 'diff_rgi_sub',
           'num_rgi_sub', 'pct_chg_sub',
           'reg_id', 'geometry']

# save the completed table/outlines into a single file for all of Alaska
difference.reset_index(names='lia_id')[columns].to_file(Path(config['outdir']) / 'alaska_lia_all_wgs84_stats.gpkg')

# split the brooks range and southern alaska outlines into separate files
o2regions = gpd.read_file(Path(config['rgi_base']) / config['rgi_ver'] / rgi_dict[config['rgi_ver']]['o2_shp'])

north = o2regions.loc[o2regions[rgi_dict[config['rgi_ver']]['o2_name']] == '01-01', 'geometry'].values[0]

is_north = difference.intersects(north)

difference.loc[is_north].reset_index(names='lia_id')[columns].to_file(Path(config['outdir']) / 'alaska_lia_north_wgs84_stats.gpkg')
difference.loc[~is_north].reset_index(names='lia_id')[columns].to_file(Path(config['outdir']) / 'alaska_lia_south_wgs84_stats.gpkg')

# find all glaciers that are within ±2% of their RGI area
small_change = difference[difference['pct_chg'].abs() < 2]
small_change.to_file(Path(config['outdir']) / 'small_changes.gpkg')

# join the disconnect point locations to the LIA and RGI outlines
disconnects['lia_id'] = disconnects.sjoin(difference)['index_right']
disconnects['rgi_id'] = disconnects.sjoin(rgi_all.ds)[rgi_id]
disconnects.to_file(Path(config['outdir']) / 'lia_disconnects.gpkg')

# aggregate the data for the regions, but this time we have to clip the glacier outlines to the mountain ranges.
inds_list = lookup_table['other_inds'].str.split(',', expand=True)

rgi_ids = pd.concat([inds_list[ind] for ind in range(len(inds_list.columns))], ignore_index=True).dropna().to_list()

for region in regions.ds.itertuples():
    clipped_lia = difference.clip(region.geometry)
    clipped_rgi = rgi_all[rgi_all[rgi_id].isin(rgi_ids)].clip(region.geometry)
    clipped_sub = rgi_sub[rgi_sub[rgi_id].isin(rgi_ids)].clip(region.geometry)

    lia_area = clipped_lia.to_crs(6393).geometry.area.sum() / 1e6
    rgi_area = clipped_rgi.to_crs(6393).geometry.area.sum() / 1e6
    sub_area = clipped_sub.to_crs(6393).geometry.area.sum() / 1e6

    clipped_lia_sub = clipped_lia.loc[clipped_lia['num_rgi_sub'] > 0].copy()
    lia_sub_area = clipped_lia_sub.to_crs(6393).geometry.area.sum() / 1e6

    regions.ds.loc[region.Index, 'lia_area'] = lia_area
    regions.ds.loc[region.Index, 'rgi_area'] = rgi_area

    regions.ds.loc[region.Index, 'diff_rgi'] = rgi_area - lia_area

    regions.ds.loc[region.Index, 'num_lia'] = len(clipped_lia.reset_index(names='lia_id').drop_duplicates('lia_id'))
    regions.ds.loc[region.Index, 'num_rgi'] = len(clipped_rgi.ds.drop_duplicates(rgi_id))

    if lia_area > 0:
        regions.ds.loc[region.Index, 'pct_chg'] = 100 * (rgi_area - lia_area) / lia_area
    else:
        regions.ds.loc[region.Index, 'pct_chg'] = np.nan

    regions.ds.loc[region.Index, 'lia_area_sub'] = lia_sub_area
    regions.ds.loc[region.Index, 'rgi_area_sub'] = sub_area

    regions.ds.loc[region.Index, 'diff_rgi_sub'] = sub_area - lia_sub_area

    regions.ds.loc[region.Index, 'num_lia_sub'] = len(
        clipped_lia_sub.reset_index(names='lia_id').drop_duplicates('lia_id'))
    regions.ds.loc[region.Index, 'num_rgi_sub'] = len(
        clipped_sub.ds.drop_duplicates(rgi_id))

    if lia_sub_area > 0:
        regions.ds.loc[region.Index, 'pct_chg_sub'] = 100 * (sub_area - lia_sub_area) / lia_sub_area
    else:
        regions.ds.loc[region.Index, 'pct_chg_sub'] = np.nan

regions.to_file(Path(config['outdir']) / 'mountainregions.gpkg')
