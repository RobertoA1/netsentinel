"""Genera las referencias en formato J.UCS ([Apellido, AA] Apellido, I.: Titulo, Revista, vol(num), paginas, anio) a partir de los metadatos de Crossref ya verificados."""
import json, re, html
A = json.load(open("../../articulo-caso26/build/crossref_raw.json")); B = json.load(open("crossref_nuevas.json"))
SRC = {**{k: v["msg"] for k, v in A.items()}, **{k: v["msg"] for k, v in B.items()}}
def ini(given): return " ".join(p[0] + "." for p in re.split(r"[\s\-]+", given.strip()) if p) if given else ""
def authors(m, maxn=6):
    au = [f"{a.get('family','')}, {ini(a.get('given',''))}".strip().rstrip(",") for a in m.get("author", [])]
    return ", ".join(au[:maxn]) + (", et al." if len(au) > maxn else "")
def clean(t): return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
def one(key, tag, year=None, venue=None, extra="", title=None):
    m = SRC[key]; yr = year or (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    t = title or clean((m.get("title") or [""])[0]); ct = venue or clean((m.get("container-title") or [""])[0])
    vol = m.get("volume"); iss = m.get("issue"); pg = (m.get("page") or m.get("article-number") or "").replace("-", "-")
    vi = (f"{vol}" if vol else "") + (f"({iss})" if iss else "")
    parts = [p for p in (ct, vi, pg, str(yr)) if p]
    return f"[{tag}] {authors(m)}: {t}, {', '.join(parts)}. https://doi.org/{m['DOI']}{extra}"
R = {
 "Akiba, 19": one("akiba2019", "Akiba, 19", title="Optuna: A Next-generation Hyperparameter Optimization Framework", venue="Proc. 25th ACM SIGKDD Int. Conf. on Knowledge Discovery & Data Mining"),
 "Bates, 24": one("bates2023", "Bates, 24", year=2024),
 "Breiman, 01": one("breiman2001", "Breiman, 01"),
 "Cantone, 24": one("cantone2024", "Cantone, 24"),
 "Chen, 16": one("chen2016", "Chen, 16", title="XGBoost: A Scalable Tree Boosting System", venue="Proc. 22nd ACM SIGKDD Int. Conf. on Knowledge Discovery & Data Mining"),
 "Dietterich, 00": one("dietterich2000", "Dietterich, 00", venue="Multiple Classifier Systems (MCS 2000), Lecture Notes in Computer Science 1857, Springer"),
 "Efron, 79": one("efron1979", "Efron, 79"),
 "Engelen, 21": one("engelen2021", "Engelen, 21", venue="Proc. 2021 IEEE Security and Privacy Workshops (SPW)"),
 "Friedman, 37": one("friedman1937", "Friedman, 37"),
 "García, 14": one("garcia2014", "García, 14"),
 "Hossain, 23": one("hossain2023", "Hossain, 23"),
 "Kapoor, 23": one("kapoor2023", "Kapoor, 23"),
 "Oškera, 25": one("oskera2025", "Oškera, 25", venue="Proc. 21st Int. Conf. on Network and Service Management (CNSM)"),
 "Roberts, 17": one("roberts2017", "Roberts, 17"),
 "Saito, 15": one("saito2015", "Saito, 15"),
 "Sarhan, 22": one("sarhan2022", "Sarhan, 22", year=2022),
 "Sharafaldin, 18": one("sharafaldin2018", "Sharafaldin, 18", venue="Proc. 4th Int. Conf. on Information Systems Security and Privacy (ICISSP)"),
 "Shinan, 21": one("shinan2021", "Shinan, 21"),
 "Sommer, 10": one("sommer2010", "Sommer, 10", venue="Proc. 2010 IEEE Symposium on Security and Privacy"),
 "Velasco-Mata, 21": one("velasco2021", "Velasco-Mata, 21"),
 "Velasco-Mata, 23": one("velasco2023", "Velasco-Mata, 23"),
 "Verkerken, 22": one("verkerken2021", "Verkerken, 22", year=2022),
 "Wilcoxon, 45": one("wilcoxon1945", "Wilcoxon, 45").replace(", 80, 1945", ", 80-83, 1945"),
}
R["Arp, 22"] = "[Arp, 22] Arp, D., Quiring, E., Pendlebury, F., Warnecke, A., Pierazzi, F., Wressnegger, C., Cavallaro, L., Rieck, K.: Dos and Don'ts of Machine Learning in Computer Security, Proc. 31st USENIX Security Symposium, 3971-3988, 2022. https://www.usenix.org/system/files/sec22-arp.pdf"
R["Bergstra, 11"] = "[Bergstra, 11] Bergstra, J., Bardenet, R., Bengio, Y., Kégl, B.: Algorithms for Hyper-Parameter Optimization, Advances in Neural Information Processing Systems 24 (NIPS 2011), 2546-2554, Granada, Spain, 2011. https://inria.hal.science/hal-00642998"
R["Bergstra, 12"] = "[Bergstra, 12] Bergstra, J., Bengio, Y.: Random Search for Hyper-Parameter Optimization, Journal of Machine Learning Research, 13, 281-305, 2012. https://dl.acm.org/doi/10.5555/2503308.2188395"
R["Cawley, 10"] = "[Cawley, 10] Cawley, G.C., Talbot, N.L.C.: On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation, Journal of Machine Learning Research, 11, 2079-2107, 2010. https://www.jmlr.org/papers/volume11/cawley10a/cawley10a.pdf"
R["COPE, 23"] = "[COPE, 23] Committee on Publication Ethics (COPE): Authorship and AI tools, COPE position statement, 13 February 2023. https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools"
R["Demšar, 06"] = "[Demšar, 06] Demšar, J.: Statistical Comparisons of Classifiers over Multiple Data Sets, Journal of Machine Learning Research, 7, 1-30, 2006. https://www.jmlr.org/papers/volume7/demsar06a/demsar06a.pdf"
R["Holm, 79"] = "[Holm, 79] Holm, S.: A Simple Sequentially Rejective Multiple Test Procedure, Scandinavian Journal of Statistics, 6(2), 65-70, 1979."
R["Pedregosa, 11"] = "[Pedregosa, 11] Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., et al.: Scikit-learn: Machine Learning in Python, Journal of Machine Learning Research, 12, 2825-2830, 2011."
R["Quiñonero-Candela, 08"] = "[Quiñonero-Candela, 08] Quiñonero-Candela, J., Sugiyama, M., Schwaighofer, A., Lawrence, N.D. (eds.): Dataset Shift in Machine Learning, The MIT Press, 2008. https://direct.mit.edu/books/edited-volume/3841/Dataset-Shift-in-Machine-Learning"
REFS = [R[k] for k in sorted(R, key=lambda s: s.lower().replace("š", "s").replace("á", "a").replace("ñ", "n").replace("ž", "z"))]
REFS = [r.replace("\u2010", "-") for r in REFS]
json.dump(REFS, open("refs.json", "w"), ensure_ascii=False, indent=1)
if __name__ == "__main__":
    for r in REFS: print(r)
