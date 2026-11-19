"""Consulta a Crossref (cliente generico, sin informacion del proyecto) los metadatos de las referencias nuevas del articulo J.UCS."""
import json, urllib.request, urllib.parse, time
DOIS = {"akiba2019": "10.1145/3292500.3330701", "chen2016": "10.1145/2939672.2939785", "breiman2001": "10.1023/A:1010933404324",
        "saito2015": "10.1371/journal.pone.0118432", "engelen2021": "10.1109/SPW53761.2021.00009", "sharafaldin2018": "10.5220/0006639801080116",
        "dietterich2000": "10.1007/3-540-45014-9_1", "roberts2017": "10.1111/ecog.02881", "efron1979": "10.1214/aos/1176344552",
        "wilcoxon1945": "10.2307/3001968", "friedman1937": "10.1080/01621459.1937.10503522"}
out = {}
for k, d in DOIS.items():
    req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(d), headers={"User-Agent": "reference-checker/1.0"})
    for i in range(4):
        try:
            r = urllib.request.urlopen(req, timeout=40); out[k] = {"status": r.status, "msg": json.load(r)["message"]}; break
        except urllib.error.HTTPError as e:
            out[k] = {"status": e.code}
            if e.code == 404: break
            time.sleep(3 * (i + 1))
        except Exception as e:
            out[k] = {"status": str(e)}; time.sleep(3 * (i + 1))
    m = out[k].get("msg", {})
    au = ", ".join(a.get("family", "") for a in (m.get("author") or [])[:4])
    print(k, out[k]["status"], "|", au, "|", (m.get("title") or [""])[0][:100], "|", (m.get("container-title") or [""])[0][:50], "|", m.get("volume"), m.get("issue"), m.get("page"), (m.get("issued", {}).get("date-parts") or [[None]])[0][0])
json.dump(out, open("crossref_nuevas.json", "w"), ensure_ascii=False, indent=1)
