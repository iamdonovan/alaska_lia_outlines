# Accelerated mass loss of glaciers across Alaska since the Little Ice Age 

This repository contains scripts used to finalize the LIA outline mapping for the following paper:

```markdown
Carrivick, J. L., R. McNabb, B. J. Davies, L. J. Larocca, E. Stephens, R. Barry, J. L. Sutherland, J. Reinthaler,
    J. Mason, and E. Lee (*in review*). Accelerated mass loss of glaciers across Alaska since the Little Ice Age.
```


## setup

### python environment 

To run `scripts/finalize_outlines.py`, the following python packages must
be installed in your environment:

- `pandas`
- `geopandas`
- `geoutils` ([readthedocs](https://geoutils.readthedocs.io/en/stable/))
- `glacmaptools` ([github](https://github.com/iamdonovan/glacmaptools))

Alternatively, use the provided `environment.yml` file to create a `conda` environment with the necessary packages.

### LIA outlines

To be able to run `scripts/finalize_outlines.py`, you will also need to download the raw LIA outline files in a
zipped format [from here]() and unzip the file in this directory. This will unpack the three `.gpkg` files into
a directory, `raw/`, where they will be read/used by the script.

### RGI outlines

You will also need to have the [Randolph Glacier Inventory](https://www.glims.org/rgi_user_guide/welcome.html) outlines
downloaded somewhere on your computer, with the following directory structure assumed:

```
rgi_base/
└─ version/
   └─ region/
```

where `version` is the version of the RGI you are comparing the LIA outlines to (v6.0 or v7.0), and `region` is a
separate directory for each of the 19 RGI sub-regions, following the naming convention for the RGI version. So, for
RGI v6.0, the outlines for Region 01 (Alaska) should be found at:

```
rgi_base/v6.0/01_rgi60_Alaska/01_rgi60_Alaska.shp
```

and for RGI v7.0, they should be found at:

```
rgi_base/v7.0/RGI2000-v7.0-G-01_alaska/RGI2000-v7.0-G-01_alaska.shp
```

### config.json

To be able to run this script on your machine, you will need to edit line 2 of `config.json` to point to the
base directory (`rgi_base`) where you have downloaded the RGI outlines.

## usage

Each of the two scripts can be run from the command line from the current directory. For
example, to run `scripts/finalize_outlines.py`:

```commandline
python scripts/finalize_outlines.py
```

## outputs

### scripts/finalize_outlines.py

`scripts/finalize_outlines.py` creates the following outputs:

- `final/alaska_lia_all_wgs84_stats.gpkg` 
- `final/alaska_lia_north_wgs84_stats.gpkg`
- `final/alaska_lia_south_wgs84_stats.gpkg`

The LIA outlines in WGS84 latitude/longitude, corresponding to all of Alaska (`all`), the North of Alaska
(RGI region 01-01), and the South of Alaska (everything outside of RGI region 01-01). Each file has the following
attributes:

- **lia_id**: a unique LIA ID for each outline
- **lia_area**: the LIA glacier area in km², calculated using the NAD83 (2011) Alaska Albers (EPSG:6393) projection
- **rgi_date**: the average source date of the RGI outlines that are intersected with the LIA outline
- **rgi_area**: the total area (in km², calculated using the same projection as the LIA outlines) of the RGI outlines
  that are intersected with the LIA outline
- **diff_rgi**: the difference between the LIA area and the RGI area
- **num_rgi**: the total number of RGI outlines that are intersected with the LIA outline
- **pct_chg**: the percent area change between the LIA outline and the RGI outlines
- **rgi_area_sub**: the total area (in km², calculated using the same projection as the LIA outlines) of the RGI outlines
  larger than 1 km² that are intersected with the LIA outline
- **diff_rgi_sub**: the difference between the LIA area and the RGI area, limited to RGI outlines larger than 1 km²
- **num_rgi_sub**: the total number of RGI outlines larger than 1 km² that are intersected with the LIA outline
- **pct_chg_sub**: the percent area change between the LIA outline and the RGI outlines that are larger than 1 km²
- **reg_id**: the ID of the mountain range where the glacier centroid is located.

`final/mountainregions.gpkg`

Polygons for each of the mountain regions, with attributes as for the individual glacier outlines,
aggregated to the mountain range level. Aggregation is done by clipping the LIA outlines to the mountain
region polygons and re-calculating based only on those glacier areas (both LIA and RGI) that are contained within
the mountain range.

- `final/lia_disconnects.gpkg`

Points representing glacier disconnections (areas where tongues have become detached from accumulation areas)
as glaciers have thinned and retreated. This file has two attributes, **lia_id** and **rgi_id**, corresponding to the
LIA and RGI ID of the glacier that has become disconnected.

- `final/small_change.gpkg`

A subset of LIA outlines that are within ±2% of their RGI area.
 
- `final/lia_rgi{version}_lookup.csv`

A lookup table with the RGI IDs for all RGI glaciers that are intersected with the LIA outlines.

