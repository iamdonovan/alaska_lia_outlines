"""
Plot LIA area vs absolute and percent area changes, with regression lines and annotated with
regression equations and coefficients of determination
"""
from pathlib import Path
import geopandas as gpd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


glacier_table = gpd.read_file(Path('final', 'alaska_lia_all_wgs84_stats.gpkg'))

mass_cols = ['dV_lia', 'dM_lia', 'SLE', 'lia_ablation', 'mb_lia', 'dV_hugonnet', 'mb_hugonnet', 'mb_acc']
glacier_table['mean_thick'] = -glacier_table['dV_lia'] / glacier_table['lia_ablation'] * 1e3

valid = np.isfinite(glacier_table.mean_thick) & (glacier_table.diff_rgi > -200)

x_reg = np.arange(-200, 1, 5)

thick_reg = stats.linregress(glacier_table.diff_rgi[valid], glacier_table.mean_thick[valid])
vol_reg = stats.linregress(glacier_table.diff_rgi[valid], -glacier_table.dV_lia[valid])

fig, axs = plt.subplots(2, 1, figsize=(4, 8))

axs[0].plot(glacier_table.diff_rgi, glacier_table.mean_thick, 'o')
axs[0].plot(x_reg, thick_reg.intercept + thick_reg.slope * x_reg, 'k', linewidth=2)

axs[0].set_xlim(-200, 0)
axs[0].set_ylim(0, 300)

axs[0].annotate(f"$f(x)$ = {thick_reg.intercept:.2f} + {thick_reg.slope:.2f}$\\,x$",
                (-200, 25), ha='left', va='bottom', xytext=(2, 0), textcoords='offset points')

axs[0].annotate(f"$R^2$ = {thick_reg.rvalue**2:.2f}",
                (-200, 0), ha='left', va='bottom', xytext=(2, 1), textcoords='offset points')

axs[0].set_ylabel('Mean thickness change (m)')


axs[1].plot(glacier_table.diff_rgi, -glacier_table.dV_lia, 'o')
axs[1].plot(x_reg, vol_reg.intercept + vol_reg.slope * x_reg, 'k', linewidth=2)

axs[1].set_xlim(-200, 0)
axs[1].set_ylim(0, 50)

axs[1].annotate(f"$f(x)$ = {vol_reg.intercept:.2f} + {vol_reg.slope:.2f}$\\,x$",
                (-200, 4), ha='left', va='bottom', xytext=(2, 0), textcoords='offset points')

axs[1].annotate(f"$R^2$ = {vol_reg.rvalue**2:.2f}",
                (-200, 0), ha='left', va='bottom', xytext=(2, 1), textcoords='offset points')

axs[1].set_ylabel('Volume change (km$^3$)')
axs[1].set_xlabel('Change in area (km$^2$)')

axs[0].annotate('A.', (0, 1), va='top', xycoords='axes fraction', xytext=(2, -2), textcoords='offset points', size=14)
axs[1].annotate('B.', (0, 1), va='top', xycoords='axes fraction', xytext=(2, -2), textcoords='offset points', size=14)

fig.savefig(Path('figs', 'Figure_SI_5.png'), dpi=200, bbox_inches='tight')