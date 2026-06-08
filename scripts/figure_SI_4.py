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

Path('figs').mkdir(parents=True, exist_ok=True)

x_reg = np.arange(1, 1202, 5)

abs_reg = stats.linregress(glacier_table.lia_area, glacier_table.diff_rgi)
pct_reg = stats.linregress(np.log(glacier_table.lia_area), glacier_table.pct_chg)

fig, axs = plt.subplots(2, 1, figsize=(5, 8))

axs[0].semilogx(glacier_table.lia_area, glacier_table.diff_rgi, 'o')
axs[0].semilogx(x_reg, abs_reg.intercept + abs_reg.slope * x_reg, 'k', linewidth=2)

axs[0].set_xlim(1, 1200)
axs[0].set_ylim(-100, 0)

axs[0].annotate(f"$f(x)$ = {abs_reg.intercept:.2f} + {abs_reg.slope:.2f}$\\,x$",
                (1, -90), ha='left', va='bottom', xytext=(2, 0), textcoords='offset points')

axs[0].annotate(f"$R^2$ = {abs_reg.rvalue**2:.2f}",
                (1, -100), ha='left', va='bottom', xytext=(2, 1), textcoords='offset points')

axs[0].set_ylabel('Absolute area change (km$^2$)')
axs[0].xaxis.set_major_formatter(ScalarFormatter())


axs[1].semilogx(glacier_table.lia_area, glacier_table.pct_chg, 'o')
axs[1].semilogx(x_reg, pct_reg.intercept + pct_reg.slope * np.log(x_reg), 'k', linewidth=2)

axs[1].set_xlim(1, 1200)
axs[1].set_ylim(-100, 0)

axs[1].annotate(f"$f(x)$ = {pct_reg.intercept:.2f} + {pct_reg.slope:.2f}$\\,ln(x)$",
                (1000, -90), ha='right', va='bottom', xytext=(2, 0), textcoords='offset points')

axs[1].annotate(f"$R^2$ = {pct_reg.rvalue**2:.2f}",
                (1000, -100), ha='right', va='bottom', xytext=(2, 1), textcoords='offset points')

axs[1].set_ylabel('Relative area change (%)')
axs[1].set_xlabel('LIA Area (km$^2$)')

axs[1].xaxis.set_major_formatter(ScalarFormatter())

axs[0].annotate('A.', (0, 1), va='top', xycoords='axes fraction', xytext=(2, -2), textcoords='offset points', size=14)
axs[1].annotate('B.', (0, 1), va='top', xycoords='axes fraction', xytext=(2, -2), textcoords='offset points', size=14)

fig.savefig(Path('figs', 'Figure_SI_4.png'), dpi=200, bbox_inches='tight')
