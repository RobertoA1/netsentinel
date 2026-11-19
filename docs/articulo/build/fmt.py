import math
NB = ' '
def d(x, k=2):
    return f"{x:.{k}f}".replace('.', ',')
def n(x):
    return f"{int(round(x)):,}".replace(',', NB)
def pc(x, k=1): return d(x*100, k) + NB + '%'
def ci(lo, hi, k=2): return f"[{d(lo,k)}; {d(hi,k)}]"
def pci(lo, hi, k=1): return f"[{d(lo*100,k)}; {d(hi*100,k)}]"
def pv(p):
    if p < 0.001: return 'p' + NB + '<' + NB + '0,001'
    return 'p' + NB + '=' + NB + d(p, 3 if p < 0.1 else 2)
def A(s): return f"⟦{s}⟧"
def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0]*len(ps); prev = 0
    for rank, i in enumerate(order):
        v = min(1.0, (len(ps)-rank)*ps[i]); prev = max(prev, v); adj[i] = prev
    return adj
