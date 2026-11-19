import json, numpy as np
D=json.load(open("datos.json")); ESC=D["escenarios"]; FL=D["flujo"]; EN=D["ensambles"]; H1=D["host_W1"]; H5=D["host_W5"]
P=D["prevalencia"]; f=lambda x:f"{x:.3f}"
ok=lambda c,m: print(("OK  " if c else "FALLA"), m)
ind=("logreg","random_forest","hist_gb","xgboost"); arb=ind[1:]
# 4.2
ok(all(FL[m]["per_esc_mean"][i]>P[str(e)] for m in ind for i,e in enumerate(ESC)), "todos > Dummy en 12 escenarios")
nueve=[1,2,3,4,5,6,9,11,13]
print("min arboles en nueve:", min(FL[m]["per_esc_mean"][ESC.index(e)] for m in arb for e in nueve), " min LR:", min(FL["logreg"]["per_esc_mean"][ESC.index(e)] for e in nueve))
for e in (7,8,12):
    v=[FL[m]["per_esc_mean"][ESC.index(e)] for m in ind]; print("esc",e,"rango",f(min(v)),f(max(v)), {m:f(FL[m]["per_esc_mean"][ESC.index(e)]) for m in ind})
print("max sd esc indiv:", {m:f(FL[m]["max_sd_esc"]) for m in ind})
print("medias:", {m:(f(FL[m]["pr_mean"]),f(FL[m]["pr_sd_seeds"]),f(FL[m]["pr_median"])) for m in ind})
print("rango4", D["rango4"]); print("friedman4", D["friedman4"])
print("ensambles:", {m:(f(EN[m]["pr_mean"]),f(EN[m]["pr_sd_seeds"]),f(EN[m]["pr_worst"]),EN[m]["pr_worst_esc"],f(EN[m]["max_sd_esc"]),f(EN[m]["bacc"]),f(EN[m]["precision"]),f(EN[m]["recall"])) for m in EN})
print("indiv extra:", {m:(f(FL[m]["bacc"]),f(FL[m]["precision"]),f(FL[m]["recall"]),f(FL[m]["pr_worst"])) for m in ind})
for m in EN: print("dif vs RF/HGB (puntos)", m, round(100*(EN[m]["pr_mean"]-FL["random_forest"]["pr_mean"]),2), round(100*(EN[m]["pr_mean"]-FL["hist_gb"]["pr_mean"]),2))
for e in (7,12): print("esc",e,"ensambles",{m:f(EN[m]["per_esc_mean"][ESC.index(e)]) for m in EN}, "HGB",f(FL["hist_gb"]["per_esc_mean"][ESC.index(e)]),"LR",f(FL["logreg"]["per_esc_mean"][ESC.index(e)]))
# host
E="LR+RF+HGB"
print("host ens:", f(EN[E]["pr_mean"]),f(EN[E]["pr_sd_seeds"]), "W1",f(H1[E]["pr_mean"]),f(H1[E]["pr_sd_seeds"]), "W5",f(H5[E]["pr_mean"]),f(H5[E]["pr_sd_seeds"]), "worst", f(EN[E]["pr_worst"]),f(H1[E]["pr_worst"]),f(H5[E]["pr_worst"]))
for e in (7,12,8,11,4):
    i=ESC.index(e); print("esc",e,"ens flujo/W1/W5", f(EN[E]["per_esc_mean"][i]),f(H1[E]["per_esc_mean"][i]),f(H5[E]["per_esc_mean"][i]))
print("LR W5 vs flujo", f(H5["logreg"]["pr_mean"]), f(FL["logreg"]["pr_mean"]))
print("host_vs_flujo W5 rf / ens", D["host_vs_flujo"]["W5 random_forest"], D["host_vs_flujo"]["W5 LR+RF+HGB"])
for r in D["intervalos"]["diferencias"]+D["intervalos"]["pares_modelos"]:
    if "random_forest" in r["comparacion"] or "LR+RF+HGB" in r["comparacion"] or "host" in r["comparacion"]: print(r["comparacion"], round(r["dif"],3), [round(x,3) for x in r["ic"]], round(r["p"],3), round(r["p_holm"],3))
# pureza
cb=json.load(open("../../validacion-externa/comprobacion_background_11.json"))
d=[abs(r["pr_ventana_pura"]-r["pr_ventana_real"]) for r in cb]; print("pureza max", max(d), "min", min(d), len(d), sorted(set(r["held_out"] for r in cb)), sorted(set(r["model"] for r in cb)))
print("flujo vs pura (efecto host):", [ (r["held_out"],r["model"],round(r["pr_ventana_pura"],3),round(r["pr_ventana_real"],3)) for r in cb if r["held_out"]==7 and r["model"]=="random_forest"])
# fondo
fo=D["fondo"]
print("alertas/100k", min(r["alertas_por_100k"] for r in fo), max(r["alertas_por_100k"] for r in fo), "fpr_bg", min(r["fpr_background"] for r in fo), max(r["fpr_background"] for r in fo))
print("prec", min(r["precision_realista"] for r in fo), max(r["precision_realista"] for r in fo), "recall", min(r["recall"] for r in fo), max(r["recall"] for r in fo))
print("pr real", min(r["pr_auc_realista"] for r in fo), max(r["pr_auc_realista"] for r in fo), "pr etiq", min(r["pr_auc_solo_etiquetados"] for r in fo), max(r["pr_auc_solo_etiquetados"] for r in fo))
print("prev completo", sorted(set((r["held_out"],round(100*r["prevalencia"],2)) for r in fo)))
print("esc3:", [(r["model"],round(r["pr_auc_realista"],3)) for r in fo if r["held_out"]==3])
print("modelos en fondo", sorted(set(r["model"] for r in fo)))
# CIC
cf={r["model"]:r for r in D["cic_flow"]}; ch={r["model"]:r for r in D["cic_host"]}
for nm,c in (("flow",cf),("host",ch)): print(nm,{m:(round(c[m]["pr_auc"],4),round(c[m]["roc_auc"],3),round(100*c[m]["fpr"],2),round(c[m]["recall"],2),round(c[m]["precision"],4),c[m]["umbral"]) for m in c})
