"""Estilo comun de figuras (sobrio, paleta de Okabe-Ito apta para daltonismo, 300 dpi, rotulos en espanol)."""
import sys, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'build'))
OK = dict(negro='#000000', naranja='#E69F00', celeste='#56B4E9', verde='#009E73', amarillo='#F0E442', azul='#0072B2', rojo='#D55E00', rosa='#CC79A7', gris='#7F7F7F')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5, 'axes.titlesize': 9, 'axes.labelsize': 8.5, 'legend.fontsize': 7.5,
                     'xtick.labelsize': 8, 'ytick.labelsize': 8, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.linewidth': 0.7, 'savefig.dpi': 300, 'figure.dpi': 150, 'axes.grid': True, 'grid.alpha': 0.25, 'grid.linewidth': 0.5})
def save(fig, name):
    fig.savefig(os.path.join(HERE, name), dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
def box(ax, x, y, w, h, text, fc='#FFFFFF', ec='#333333', fs=7.5, bold=False, lw=0.9, ls='-'):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.01,rounding_size=0.12', fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=fs, fontweight='bold' if bold else 'normal', wrap=True, linespacing=1.15)
def arrow(ax, p, q, text=None, rad=0.0, color='#333333', fs=6.5, off=(0, 0.12), ls='-'):
    a = FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=8, lw=0.9, color=color, connectionstyle=f'arc3,rad={rad}', ls=ls)
    ax.add_patch(a)
    if text:
        ax.text((p[0]+q[0])/2 + off[0], (p[1]+q[1])/2 + off[1], text, fontsize=fs, ha='center', va='center', color=color)
